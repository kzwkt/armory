#!/usr/bin/python

from included.ReportTemplate import ReportTemplate
from database.repositories import PortRepository
import pdb
import json



class Report(ReportTemplate):
    '''
    This report displays all of the certificates
    from https boxes.
    '''

    markdown = ['###', '`']

    name = "CertReport"
    def __init__(self, db):
        self.Port = PortRepository(db)
        
    def set_options(self):
        super(Report, self).set_options()
        self.options.add_argument('-t', '--tool', help="Source tool")

    def run(self, args):
        
        results = []
        services = self.Port.all(name='https')
        certs = {}
        for s in services:
            if s.meta.get('sslcert', False):
                for k in s.meta['sslcert'].keys():
                    cert = s.meta['sslcert'][k]
                    # pdb.set_trace()
                    if not certs.get(cert, False):
                        certs[cert] = []

                    certs[cert].append(k + ':' + str(s.port_number))

        for k in certs.keys():
            results.append(', '.join(sorted(list(set(certs[k])))))
            for l in k.split('\n'):
                results.append('\t' + l)
        
        self.process_output(results, args)



    