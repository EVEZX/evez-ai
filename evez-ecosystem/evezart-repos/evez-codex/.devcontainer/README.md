# Containerized Development

We provide the following options to facilitate Codex development in a container. This is particularly useful for verifying the Linux build when working on a macOS host.

## GitHub Codespaces

The devcontainer configuration is optimized for GitHub Codespaces and includes:

### Languages & Tooling
- **Node.js** (v22) with pnpm, TypeScript, and tsx
- **Rust** with cargo, rustfmt, clippy, and rust-analyzer
- **Go** (1.22)
- **Python** 3 with pip
- **Java** 21 with Maven and Gradle
- **Docker**

### Canonical Hashing Libraries
The devcontainer includes pre-installed canonical JSON serialization libraries:
- **Node.js**: `json-canonicalize` (RFC 8785 implementation)
- **Python**: `rfc8785` (official RFC 8785 implementation)
- **Go**: `webpki/jcs` (can be installed via `go get`)
- **Rust**: `serde_jcs` (add to Cargo.toml)
- **Java**: WebPKI/JCS (available via Maven)

### Quick Start with Codespaces
1. Click the green **Code** button on GitHub
2. Select **Codespaces** tab
3. Click **Create codespace on main**
4. Wait for the container to build (includes all tooling)
5. Run ops-stack tests: `cd ops-stack && pnpm test`
6. Run deployment script: `./deploy-ops-stack.sh`

## Docker

To build the Docker image locally for x64 and then run it with the repo mounted under `/workspace`:

```shell
CODEX_DOCKER_IMAGE_NAME=codex-linux-dev
docker build --platform=linux/amd64 -t "$CODEX_DOCKER_IMAGE_NAME" ./.devcontainer
docker run --platform=linux/amd64 --rm -it -e CARGO_TARGET_DIR=/workspace/codex-rs/target-amd64 -v "$PWD":/workspace -w /workspace/codex-rs "$CODEX_DOCKER_IMAGE_NAME"
```

Note that `/workspace/target` will contain the binaries built for your host platform, so we include `-e CARGO_TARGET_DIR=/workspace/codex-rs/target-amd64` in the `docker run` command so that the binaries built inside your container are written to a separate directory.

For arm64, specify `--platform=linux/arm64` instead for both `docker build` and `docker run`.

Currently, the `Dockerfile` works for both x64 and arm64 Linux, though you need to run `rustup target add x86_64-unknown-linux-musl` yourself to install the musl toolchain for x64.

## VS Code

VS Code recognizes the `devcontainer.json` file and gives you the option to develop Codex in a container. Currently, `devcontainer.json` builds and runs the `arm64` flavor of the container.

From the integrated terminal in VS Code, you can build either flavor of the `arm64` build (GNU or musl):

```shell
cargo build --target aarch64-unknown-linux-musl
cargo build --target aarch64-unknown-linux-gnu
```

### VS Code Extensions
The devcontainer includes the following extensions:
- rust-analyzer (Rust language server)
- Even Better TOML
- Go (Go language server)
- Python (Python language server)
- ESLint (JavaScript/TypeScript linting)
- Prettier (Code formatting)
- Java Extension Pack
- Java Language Support
