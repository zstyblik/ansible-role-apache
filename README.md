# Ansible role apache

**READ ME FIRST:** Probably for the last 50 people or so which are still using
Ansible I wholeheartedly recommend to use [geerlingguy.apache] role. Why?
Because it's tested, maintained and covers a lot of, if not the most of, use
cases.

---

This is yet another ansible role for management of Apache's [httpd]. Inspiration
for this role was and is [puppetlabs-apache] module. Another one is
aforementioned Geerlingguy's ansible role [geerlingguy.apache].

Since nobody is going to use this anyway(Ansible isn't used anymore and neither
is httpd) I'm afraid that's it. Only supported OS at this moment is Debian.
I might add support for some other OS, if and when I'm bored.

#### Features

* richer httpd and virtual host configuration(perhaps it's too much)
* generate `ports.conf` from virtual hosts
* allow to enable/disable config files
* allow to enable/disable modules

#### Known limitations

##### Ports

* if there are no virtual hosts, httpd should listen at port 80 and 443 as is
  by default in Debian.
* ports are generated **ONLY** from managed(defined) virtual hosts. It's
  possible to define additional `Listen` directives via `apache_confs`.

##### Virtual Hosts

Virtual host filename is assembled from priority, protocol and servername. If
any of these change, new filename will be created and the old one will be left
behind since unmanaged stuff is left alone. This is kind of suboptimal.

One way around this is either duplicate the whole virtual host configuration or
create a minimal stub with identical combination of port, servername and
ssl/no-ssl and `state: absent`. Then the former virtual host should get
disabled and new one deployed.

## Requirements

None.

## Role variables

See `defaults/main.yml`. There is also `specs/apache_vhost_argument_specs.yml`
which should give you some idea about configuration options and possibilities
regarding virtual hosts.

## Dependencies

There are no extra dependencies as far as Ansible goes.

## Example Playbook

```
- hosts: all
  vars:
    apache_vhosts:
      - servername: "local1.dev"
        port: 80
        docroot: "/var/www/html"
        rewrites:
          - rewrite_rule: ["^/.*$ https://localhost1 [R=302,L]"]

      - servername: "localhost1"
        serveradmin: "root@example.com"
        port: 443
        docroot: "/var/www/html"
        directories:
          - path: "/var/www/html"
            allowoverride: ["None"]
            directoryindex: "index.php"
            require: "all granted"
            addhandlers:
              - handler: "application/x-httpd-php"
                extensions:
                  - "\.php"

          - provider: "location"
            path: "/README"
            require: "all denied"
        ssl:
          - ssl_cert: "/etc/ssl/certs/ssl-cert-snakeoil.pem"
            ssl_key: "/etc/ssl/private/ssl-cert-snakeoil.key"
            ssl_cacerts_dir: "/etc/ssl/certs"

      - servername: "local2.dev"
        state: absent
        listen_ip: "127.0.0.1"
        port: 8080
        docroot: "/var/www/html"
        error_log_format24:
          - format: "[%{uc}t] [%-m:%-l] [R:%L] [C:%{C}L] %7F: %E: %M"
          - flag: request
            format: "[%{uc}t] [R:%L] Request %k on C:%{c}L pid:%P tid:%T"

    apache_mods:
      - name: rewrite
        state: present
      - name: ssl
        conf_content: |
          SSLProtocol all -SSLv2 -SSLv3 -TLSv1

    apache_confs:
      - name: serve-cgi-bin
        state: absent
      - name: my_config
        conf_content: |
          TraceEnable On
  roles:
     - role: zstyblik.apache
```

## License

MIT

[geerlingguy.apache]: https://github.com/geerlingguy/ansible-role-apache/tree/master
[httpd]: https://httpd.apache.org
[puppetlabs-apache]: https://forge.puppet.com/modules/puppetlabs/apache/readme
