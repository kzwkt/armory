#!/usr/bin/python

from database.repositories import BaseDomainRepository, DomainRepository, UserRepository
from included.ModuleTemplate import ModuleTemplate
import subprocess
from included.utilities import which
import shlex
import os
import pdb
import xmltodict
from tld import get_tld
import csv
import string

def remove_binary(txt):
    return ''.join([t for t in txt if t in string.printable])

class Module(ModuleTemplate):
    
    name = "LinkedInt"

    def __init__(self, db):
        self.db = db
        self.BaseDomain = BaseDomainRepository(db, self.name)
        self.User = UserRepository(db, self.name)

    def set_options(self):
        super(Module, self).set_options()

        self.options.add_argument('-d', '--domain', help="Domain to add onto email")
        self.options.add_argument('-c', '--company_id', help="Company ID to search")
        self.options.add_argument('-C', '--restrict', help="Restrict to company filter", action="store_true")
        self.options.add_argument('-k', '--keywords', help="Keywords to search for")
        self.options.add_argument('-o', '--output_path', help="Path which will contain program output (relative to base_path in config", default=self.name)
        self.options.add_argument('-s', '--rescan', help="Rescan domains that have already been scanned", action="store_true")
        
    def run(self, args):
        # pdb.set_trace()        
        if not args.binary:
            self.binary = which.run('LinkedInt.py')

        else:
            self.binary = which.run(args.binary)

        if not self.binary:
            print("LinkedInt binary not found. Please explicitly provide path with --binary")


        if args.domain:
            created, domain = self.BaseDomain.find_or_create(domain=args.domain)
            self.process_domain(domain, args)
            self.BaseDomain.commit()
        
                
    def process_domain(self, domain_obj, args):

        domain = domain_obj.domain

        if args.output_path[0] == "/":
            output_path = os.path.join(self.base_config['PROJECT']['base_path'], args.output_path[1:])
        else:
            output_path = os.path.join(self.base_config['PROJECT']['base_path'], args.output_path)

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        output_path = os.path.join(output_path, "%s-linkedint" % domain.replace('.', '_') )
        
        command_args = " -o %s" % output_path
        
        command_args += " -e %s" % domain
        command_args += " -u %s" % args.keywords

        if args.company_id:
            command_args += " -i %s " % args.company_id

        if args.restrict:
            command_args += " -c "
        # if args.threads:
        #     command_args += " -t " + args.threads
        current_dir = os.getcwd()

        new_dir = '/'.join(self.binary.split('/')[:-1])

        os.chdir(new_dir)

        cmd = shlex.split("python " + self.binary + command_args)
        print("Executing: %s" % ' '.join(cmd))
        
        res = subprocess.Popen(cmd).wait()
        
        os.chdir(current_dir)    
        count = 0        
        with open(output_path + '.csv') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=",", quotechar='"')

            for row in csvreader:
                count += 1
                if self.User.find(email=row[3]):
                    created, user = self.User.find_or_create(email=remove_binary(row[3]))

                    user.first_name = remove_binary(row[0])
                    user.last_name = remove_binary(row[1])
                    user.job_title = remove_binary(row[4])
                    user.location = remove_binary(row[5])
                    

                else:
                    created, user = self.User.find_or_create(first_name=remove_binary(row[0]), last_name=remove_binary(row[1]), domain=domain_obj)
                    if created:
                        print("New user: %s %s" % (remove_binary(row[0]), remove_binary(row[1])))

                    user.email = remove_binary(row[3])
                    user.job_title = remove_binary(row[4])
                    user.location = remove_binary(row[5])
                user.update()

        print("%s found and imported" % count)
        self.User.commit()                