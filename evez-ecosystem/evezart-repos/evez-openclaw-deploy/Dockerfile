FROM openclaw/openclaw:latest

USER root
COPY openclaw.json /opt/evez-openclaw-deploy/openclaw.json
COPY workspace /opt/evez-openclaw-deploy/workspace
COPY runtime /opt/evez-openclaw-deploy/runtime
COPY docker/openclaw-entrypoint.sh /usr/local/bin/evez-openclaw-entrypoint
RUN chmod +x /usr/local/bin/evez-openclaw-entrypoint

ENTRYPOINT ["evez-openclaw-entrypoint"]
CMD ["node", "dist/index.js", "gateway", "--port", "18789", "--bind", "lan"]
