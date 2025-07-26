# Build stage: use official Golang image
FROM golang:1.24 AS builder

WORKDIR /go/src/app

# Copy go.mod and go.sum first for dependency caching
COPY src/go.mod ./
# (Optional: COPY src/go.sum ./ if you have a go.sum file)

# Download dependencies
RUN go mod download

# Copy the rest of the source code
COPY src/ ./

# Build the Go binary
RUN CGO_ENABLED=0 go build -o /go/bin/app

# Use minimal runtime image
FROM gcr.io/distroless/static

USER nonroot:nonroot

# Copy the built binary from the builder stage
COPY --from=builder --chown=nonroot:nonroot /go/bin/app /

# Expose the port
EXPOSE 8080

# Run the web service on container startup
CMD [ "/app" ]