#!/usr/bin/python
DOCUMENTATION = '''
---
module: ezjail
author: Tom Lazar
short_description: Manage FreeBSD jails
requirements: [ zfs ]
description:
    - Manage FreeBSD jails
'''

from collections import OrderedDict


def list_jails(output):
    ''' parses the output from calling `ezjail-admin list` and returns a python data structure'''
    jails = OrderedDict()
    for line in output.split('\n')[2:-1]:
        entry = dict(zip(['status', 'jid', 'ip', 'name', 'path'], line.split()))
        jails[entry.pop('name')] = entry
    return jails


class Ezjail(object):

    platform = 'FreeBSD'

    def __init__(self, module):
        self.module = module
        self.changed = False
        self.state = self.module.params.pop('state')
        self.name = self.module.params.pop('name')
        self.cmd = self.module.get_bin_path('ezjail-admin', required=True)

    def ezjail_admin(self, command, *params):
        return self.module.run_command(' '.join(['sudo', self.cmd, command] + list(params)))

    def exists(self):
        (rc, out, err) = self.ezjail_admin('list')
        return self.name in list_jails(out)

    def create(self):
        result = dict()
        if self.module.check_mode:
            self.changed = True
            return result
        (rc, out, err) = self.ezjail_admin('create', self.name, self.module.params['ip_addr'])
        if rc == 0:
            self.changed = True
        else:
            self.changed = False
            result['failed'] = True
            result['msg'] = "Could not create jail. %s%s" % (out, err)
        return result

    def destroy(self):
        raise NotImplemented

    def __call__(self):

        result = dict(name=self.name, state=self.state)

        if self.state == 'present':
            if not self.exists():
                result.update(self.create())
        elif self.state == 'absent':
            if self.exists():
                self.destroy()

        result['changed'] = self.changed
        return result


MODULE_SPECS = dict(
    argument_spec=dict(
        name=dict(required=True, type='str'),
        state=dict(default='present', choices=['present', 'absent'], type='str'),
        ip_addr=dict(required=True, type='str'),
        ),
    supports_check_mode=True
)


def main():
    module = AnsibleModule(**MODULE_SPECS)
    result = Ezjail(module)()
    if 'failed' in result:
        module.fail_json(**result)
    else:
        module.exit_json(**result)

# include magic from lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
if __name__ == "__main__":
    main()
