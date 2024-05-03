FROM grafana/grafana


COPY /src/docker/grafana/datasource.yml /etc/grafana/provisioning/datasources/
COPY /src/docker/grafana/dashboards.yml /etc/grafana/provisioning/dashboards/
COPY /src/docker/grafana/default-dashboard.json /var/lib/grafana/dashboards/
