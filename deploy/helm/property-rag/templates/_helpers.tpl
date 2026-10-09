{{/*
Expand the name of the chart.
*/}}
{{- define "property-rag.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "property-rag.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "property-rag.labels" -}}
helm.sh/chart: {{ include "property-rag.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
