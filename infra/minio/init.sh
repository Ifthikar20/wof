#!/bin/sh
# Create local buckets: uploads stay private; processed media is anonymously readable
# (in production this is an R2/S3 bucket reachable only through the CDN).
set -e
mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb --ignore-existing local/wof-uploads
mc mb --ignore-existing local/wof-media
mc anonymous set none local/wof-uploads
mc anonymous set download local/wof-media
echo "buckets ready"
