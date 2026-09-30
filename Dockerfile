FROM odoo:19 

USER root

RUN mkdir -p /etc/odoo /etc/odoo/customs /etc/odoo/themes

COPY ./customs /etc/odoo/customs
COPY ./themes /etc/odoo/themes
COPY ./odoo.conf /etc/odoo

EXPOSE 8069

ENTRYPOINT ["odoo","-c","/etc/odoo/odoo.conf"]