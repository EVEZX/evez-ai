# EVEZ-OS Oracle Cloud Free Tier — Terraform Configuration
# Deploys: ARM64 Ampere A1 (4 OCPU, 24GB RAM) + VCN + Security + Cloud-Init
# Cost: $0.00 (Always Free)

# ============================================================
# PROVIDER
# ============================================================

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# ============================================================
# VARIABLES
# ============================================================

variable "tenancy_ocid" {
  description = "Oracle Cloud tenancy OCID"
  type        = string
}

variable "user_ocid" {
  description = "Oracle Cloud user OCID"
  type        = string
}

variable "fingerprint" {
  description = "API key fingerprint"
  type        = string
}

variable "private_key_path" {
  description = "Path to API private key"
  type        = string
  default     = "~/.oci/oci_api_key.pem"
}

variable "region" {
  description = "Oracle Cloud region (e.g., us-phoenix-1, us-ashburn-1)"
  type        = string
  default     = "us-phoenix-1"
}

variable "compartment_ocid" {
  description = "Compartment OCID (defaults to tenancy)"
  type        = string
  default     = ""
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

variable "instance_name" {
  description = "Compute instance display name"
  type        = string
  default     = "evez-os"
}

variable "availability_domain" {
  description = "Availability domain (e.g., Uocm:PHX-AD-1)"
  type        = string
  default     = ""
}

# ============================================================
# DATA SOURCES
# ============================================================

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid != "" ? var.compartment_ocid : var.tenancy_ocid
}

data "oci_core_images" "ubuntu_arm" {
  compartment_id           = var.compartment_ocid != "" ? var.compartment_ocid : var.tenancy_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

locals {
  compartment_ocid    = var.compartment_ocid != "" ? var.compartment_ocid : var.tenancy_ocid
  availability_domain = var.availability_domain != "" ? var.availability_domain : data.oci_identity_availability_domains.ads.availability_domains[0].name
  image_id            = data.oci_core_images.ubuntu_arm.images[0].id
}

# ============================================================
# NETWORKING — VCN
# ============================================================

resource "oci_core_vcn" "evez_vcn" {
  compartment_id = local.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "evez-vcn"
  dns_label      = "evezvcn"
}

resource "oci_core_internet_gateway" "evez_igw" {
  compartment_id = local.compartment_ocid
  vcn_id         = oci_core_vcn.evez_vcn.id
  display_name   = "evez-internet-gateway"
  enabled        = true
}

resource "oci_core_route_table" "evez_rt" {
  compartment_id = local.compartment_ocid
  vcn_id         = oci_core_vcn.evez_vcn.id
  display_name   = "evez-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.evez_igw.id
  }
}

# ============================================================
# SECURITY LIST — Open EVEZ Ports
# ============================================================

resource "oci_core_security_list" "evez_security" {
  compartment_id = local.compartment_ocid
  vcn_id         = oci_core_vcn.evez_vcn.id
  display_name   = "evez-security-list"

  # --- EGRESS: allow all outbound ---
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
    stateless   = false
  }

  # --- INGRESS: SSH ---
  ingress_security_rules {
    protocol    = "6"  # TCP
    source      = "0.0.0.0/0"
    stateless   = false
    tcp_options {
      min = 22
      max = 22
    }
  }

  # --- INGRESS: HTTP ---
  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    tcp_options {
      min = 80
      max = 80
    }
  }

  # --- INGRESS: HTTPS ---
  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    tcp_options {
      min = 443
      max = 443
    }
  }

  # --- INGRESS: EVEZ services 8080-8100 ---
  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    tcp_options {
      min = 8080
      max = 8100
    }
  }

  # --- INGRESS: EVEZ main node port 18789 ---
  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    tcp_options {
      min = 18789
      max = 18789
    }
  }
}

# ============================================================
# SUBNET
# ============================================================

resource "oci_core_subnet" "evez_subnet" {
  compartment_id    = local.compartment_ocid
  vcn_id            = oci_core_vcn.evez_vcn.id
  cidr_block        = "10.0.1.0/24"
  display_name      = "evez-subnet"
  dns_label         = "evezsubnet"
  route_table_id    = oci_core_route_table.evez_rt.id
  security_list_ids = [oci_core_security_list.evez_security.id]
}

# ============================================================
# COMPUTE INSTANCE — Ampere A1 (4 OCPU, 24GB RAM)
# ============================================================

resource "oci_core_instance" "evez_os" {
  compartment_id      = local.compartment_ocid
  availability_domain = local.availability_domain
  display_name        = var.instance_name
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 4
    memory_in_gbs = 24
  }

  source_details {
    source_type             = "image"
    source_id               = local.image_id
    boot_volume_size_in_gbs = 47  # within free tier
  }

  create_vnic_details {
    subnet_id    = oci_core_subnet.evez_subnet.id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(file("${path.module}/cloud-init.yaml"))
  }

  # Retry on capacity issues (ARM instances can be scarce)
  timeouts {
    create = "90m"
  }
}

# ============================================================
# BLOCK VOLUME — 200GB (Free Tier)
# ============================================================

resource "oci_core_volume" "evez_data" {
  compartment_id      = local.compartment_ocid
  availability_domain = local.availability_domain
  display_name        = "evez-data-vol"
  size_in_gbs         = 200

  # Use free-tier shape
  vpus_per_gbe = 0  # Lower performance tier, still free
}

resource "oci_core_volume_attachment" "evez_data_attach" {
  attachment_type = "paravirtualized"
  compartment_id  = local.compartment_ocid
  instance_id     = oci_core_instance.evez_os.id
  volume_id       = oci_core_volume.evez_data.id
  display_name    = "evez-data-attachment"
}

# ============================================================
# OUTPUTS
# ============================================================

output "instance_public_ip" {
  description = "Public IP of the EVEZ-OS instance"
  value       = oci_core_instance.evez_os.public_ip
}

output "instance_ocid" {
  description = "OCID of the EVEZ-OS instance"
  value       = oci_core_instance.evez_os.id
}

output "vcn_id" {
  description = "VCN OCID"
  value       = oci_core_vcn.evez_vcn.id
}

output "block_volume_id" {
  description = "Block volume OCID (200GB data)"
  value       = oci_core_volume.evez_data.id
}
