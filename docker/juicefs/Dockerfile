FROM alpine:3.19

# 安装依赖 + FUSE
RUN apk add --no-cache fuse3 fuse3-libs ca-certificates curl tini

# 安装 JuiceFS
RUN curl -sSL https://d.juicefs.com/install | sh - && \
    cp /usr/local/bin/juicefs /usr/bin/juicefs

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
