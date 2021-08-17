from os import environ as env

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template

from cabot3.cabotapp.alert import AlertPlugin


email_template = """Service {{ service.name }} {{ scheme }}://{{ host }}{% url 'service' pk=service.id %} {% if service.overall_status != service.PASSING_STATUS %}alerting with status: {{ service.overall_status }}{% else %}is back to normal{% endif %}.
{% if service.overall_status != service.PASSING_STATUS %}
CHECKS FAILING:{% for check in service.all_failing_checks %}
  FAILING - {{ check.name }} - Type: {{ check.check_category }} - Importance: {{ check.get_importance_display }}{% endfor %}
{% if service.all_passing_checks %}
Passing checks:{% for check in service.all_passing_checks %}
  PASSING - {{ check.name }} - Type: {{ check.check_category }} - Importance: {{ check.get_importance_display }}{% endfor %}
{% endif %}
{% endif %}
"""


class EmailAlert(AlertPlugin):
    name = "Email"
    author = "Jonathan Balls"

    def send_alert(self, service, users, duty_officers):
        emails = set([u.email for u in users if u.email])

        c = Context({
            'service': service,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME
        })
        if service.overall_status != service.PASSING_STATUS:
            if service.overall_status == service.CRITICAL_STATUS:
                emails.update([u.email for u in duty_officers if u.email])
            subject = '%s status for service: %s' % (
                service.overall_status, service.name)
        else:
            subject = 'Service back to normal: %s' % (service.name,)
        if not emails:
            return
        t = Template(email_template)
        send_mail(
            subject=subject,
            message=t.render(c),
            from_email='Cabot <%s>' % env.get('CABOT_FROM_EMAIL'),
            recipient_list=list(emails),
        )
