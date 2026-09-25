"""
Dev-only views that stand in for object storage when ``LOCAL_MEDIA_ROOT`` is set:

* ``POST /api/v1/media/local-upload`` receives the browser's multipart upload. It is
  authorised by the signed token issued with the upload (exactly like an S3 POST policy),
  so it is CSRF-exempt on purpose: no cookie is involved. The token pins the key and content
  type and expires after 5 minutes; the body is capped at UPLOAD_MAX_BYTES.
* ``GET /local-media/<key>`` serves processed variants (what the CDN does in production).

Both are wired up only when the setting exists (wof/settings/local.py), never in prod.
"""

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import storage


@csrf_exempt
@require_POST
def local_upload(request):
    token = storage.read_upload_token(request.POST.get("token", ""))
    upload = request.FILES.get("file")
    if token is None or upload is None:
        return JsonResponse({"error": "invalid or expired upload token"}, status=403)
    if request.POST.get("Content-Type", upload.content_type) != token["ct"]:
        return JsonResponse({"error": "content type does not match the upload policy"}, status=400)
    if upload.size > settings.UPLOAD_MAX_BYTES:
        return JsonResponse({"error": "file too large"}, status=413)
    try:
        storage.local_store_upload(token["key"], token["ct"], upload.chunks())
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"ok": True}, status=201)


@require_GET
def local_media(request, key: str):
    try:
        path = storage._local_path(key, public=True)
    except ValueError as exc:
        raise Http404 from exc
    if not path.is_file():
        raise Http404
    response = FileResponse(open(path, "rb"), content_type="image/webp")
    response["Cache-Control"] = "public, max-age=3600"
    response["X-Content-Type-Options"] = "nosniff"
    return response
