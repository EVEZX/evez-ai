# Evez OS VCL configuration

sub vcl_recv {
    # Example rule for Evez OS
    if (req.url ~ "^/static/") {
        return (hash);
    }
}
