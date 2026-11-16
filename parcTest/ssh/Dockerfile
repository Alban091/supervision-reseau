FROM alpine:3.24

RUN apk add --no-cache openssh
RUN ssh-keygen -A
# sshd en arriere-plan et sleep infinity garde le conteneur allume
CMD ["sh", "-c", "/usr/sbin/sshd && exec sleep infinity"]
