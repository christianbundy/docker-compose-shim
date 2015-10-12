#!/usr/bin/env python3

import os
import yaml
from docopt import docopt


class shdocker:
    services = None

    def __init__(self, path='docker-compose.yml'):
        with open(path, 'r') as stream:
            self.services = yaml.load(stream)
            self.start()

    def link(self, service, target):
        if target == service:
            if 'links' in self.services[service]:
                for link in self.services[service]['links']:
                    self.link(service, link)
        else:
            cmd = '{}_link="$({})" '.format(target, self.services[target]['config']['cmd'])
            self.services[service]['config']['links'].append(cmd)


    def start(self):
        for service in self.services:
            cmd = ''
            self.services[service]['config'] = {
                'options': [],
                'image': '',
                'command': '',
                'args': [],
                'links': []
            }

            parser = parsers(self.services)
            self.services = parser.parse(service)

            parts = ['docker run -d ',
                     ' '.join(self.services[service]['config']['options']),
                     ' ' + self.services[service]['config']['image'],
                     ' ' + self.services[service]['config']['command'],
                     ' '.join(self.services[service]['config']['args'])
                     ]

            run = ''.join(parts)
            cmd += run
            self.services[service]['config']['cmd'] = cmd

        for service in self.services:
            cmd = ''
            self.link(service, service)
            links = ''.join(self.services[service]['config']['links'])

            cmd += self.services[service]['config']['cmd']
            print('# {}'.format(service))

            print('{} {}'.format(links, cmd))

class parsers:
    def __init__ (self, services):
        self.services = services

    def parse(self, service):
        for key in self.services[service]:
            cmd = ''
            try:
                val = self.services[service][key]
                ret = getattr(self, key)(service, val)
                if ret:
                    cmd += ret
            except AttributeError:
                raise AttributeError("No parser found for {}".format(service))
        return self.services

    def image(self, service, image):
        self.services[service]['config']['image'] = image

    def command(self, service, command):
        self.services[service]['config']['command'] = command

    def build(self, service, build):
        self.services[service]['config']['image'] = service
        return 'docker build -t {} {} && '.format(service, build)

    def ports(self, service, ports):
        for port in ports:
            self.services[service]['config']['options'].append('-p {}'.format(port))

    def restart(self, service, restart):
        self.services[service]['config']['options'].append('--restart={}'.format(restart))

    def volumes(self, service, volumes):
        for volume in volumes:
            self.services[service]['config']['options'].append('-v {}'.format(volume))

    def environment(self, service, environment):
        for variable in environment:
            if environment[variable]:
                value = '${}'.format(environment[variable])
            else:
                value = variable
            self.services[service]['config']['options'].append('-e "{}={}"'.format(variable, value))

    def volumes_from(self, service, volumes_from):
        for volumes_from_service in volumes_from:
            self.services[service]['config']['options'].append('--volumes-from {}'.format(volumes_from_service))

    def links(self, service, links):
        for link in links:
            self.services[service]['config']['options'].append('--link "${}_link:{}"'.format(link, link))

    def config(self, service, links):
        pass

shd = shdocker('docker-compose.yml')
