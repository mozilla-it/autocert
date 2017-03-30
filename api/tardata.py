#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob

#from utils import tar
from utils import sift
from utils.dictionary import merge, body

from utils.format import fmt, pfmt

from utils.cert import Cert

class DecomposeTarpathError(Exception):
    def __init__(self, tarpath):
        msg = fmt('error decomposing tarpath={tarpath}')
        super(DecomposeTarpathError, self).__init__(msg)

class Tardata(object):

    def __init__(self, tarpath, verbosity):
        self._tarpath = str(tarpath)
        self.verbosity = verbosity

    @property
    def tarpath(self):
        return self._tarpath

    @property
    def tarfiles(self):
        return glob.glob(str(self._tarpath + '/*.tar.gz'))

    @property
    def cert_names(self):
        return [self.tarfile_to_cert_name(tarfile) for tarfile in self.tarfiles]

    def decompose_tarfile(self, tarfile):
        if tarfile.startswith(self.tarpath) and tarfile.endswith('tar.gz'):
            ext = '.tar.gz'
            cert_name = os.path.basename(tarfile)[0:-len(ext)]
            return self.tarpath, cert_name, ext
        raise DecomposeTarpathError(tarpath)

    def cert_name_to_tarfile(self, cert_name):
        return self.tarpath + '/' + cert_name + '.tar.gz'

    def tarfile_to_cert_name(self, tarfile):
        _, cert_name, _ = self.decompose_tarfile(tarfile)
        return cert_name

    def load_cert(self, cert_name):
        cert = Cert.load(self.tarpath, cert_name)
        return cert

    def load_certs(self, timestamp, *cert_name_pns):
        certs = []
        for cert_name in sorted(sift.fnmatches(self.cert_names, cert_name_pns)):
            cert = self.load_cert(cert_name)
            if timestamp == None or cert.expiry > timestamp:
                certs += [cert]
        return certs
