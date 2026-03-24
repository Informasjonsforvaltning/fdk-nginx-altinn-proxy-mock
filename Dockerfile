FROM nginx:alpine

ENV TZ=Europe/Oslo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apk add --no-cache python3

COPY nginx.conf.template /etc/nginx/nginx.conf.template

COPY mockdata /mockdata
COPY mockdataV2 /mockdataV2
COPY scripts/v2_mock_server.py /scripts/v2_mock_server.py

EXPOSE 8080

COPY entrypoint.sh /

RUN chmod +x /entrypoint.sh /scripts/v2_mock_server.py
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
