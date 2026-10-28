# Husguiden – one image, any number of independent house guides (one container + one volume each).
# Build:  docker build -t husguiden .
# Run:    see compose.yaml and docs/DEPLOY.md
FROM python:3.12-slim
WORKDIR /app
COPY . .
# every house in houses/ + the family page + the portal demo → /app/dist (no network needed: three.js is vendored)
RUN python3 -I tools/build.py && useradd -r -u 10001 husguiden && mkdir -p /data && chown husguiden /data
USER husguiden
ENV PORT=8080 PUBLIC=1 SITE=family SEED="houses/joanmiro87 houses/hulehallar:hamra-"
VOLUME /data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python3 -c "import urllib.request,os;urllib.request.urlopen('http://127.0.0.1:'+os.environ['PORT']+'/health',timeout=3)"
CMD ["sh", "server/start.sh"]
