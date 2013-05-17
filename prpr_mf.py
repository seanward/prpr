#!/usr/bin/env python3

# prpr_mf.py, a part of PR-PR (previously known as PaR-PaR), a biology-friendly language for liquid-handling robots
# Author: Nina Stawski, nstawski@lbl.gov, me@ninastawski.com
# Copyright 2012-2013, Lawrence Berkeley National Laboratory
# http://github.com/JBEI/prpr/blob/master/license.txt

__author__ = 'Nina Stawski'
__contact__ = 'me@ninastawski.com'
__version__ = '0.6'

#microfluidics support for PRPR

import os
from prpr import *
from copy import deepcopy

class PRPR:
    def __init__(self, ID):
        self.expID = ID
        db = DatabaseHandler(ID)
        self.transfers = db.transfers
        self.mfWellConnections = db.mfWellConnections
        self.mfWellLocations = db.mfWellLocations
        self.logger = []
        self.robotConfig = []
        self.transactions = []
        self.volumesList = []
        self.createTransfer()
        self.saveLog()
        self.saveConfig()

    def createTransfer(self):
        allTransfers = self.transfers
        unparsedTransfers = []
        for i, transfer in enumerate(allTransfers):
            trType = transfer['type']
            els = transfer['info']
            if trType == 'command':
                self.parseCommand(els)
            elif trType == 'transfer':
                transfers = self.parseTransfer(els, i)
                for element in transfers:
                    unparsedTransfers.append(element)
        self.saveTransfers(unparsedTransfers)

    def parseTransfer(self, transferList, transferNumber):
        transfers = []
        from_ = transferList[0]['source']['well']
        to_ = transferList[len(transferList) - 1]['destination']['well']
        print(from_, to_)
        for t, transfer in enumerate(transferList):
            config = {}
            waitNum = str(transferNumber) + '_o'
            trNum = str(transferNumber) + '_w_' + from_ + '_to_' + to_ + '_o'
            config['name'] = 'tr' + trNum
            config['details'] = ['tr' + trNum]
            source = transfer['source']['well']
            destination = transfer['destination']['well']
            wait = transfer['wait']
            config['times'] = int(transfer['times'])
            transferPath = self.findPath(source, destination)
            print('src dst trlist', transferPath, source, destination, transferList)
            p = 0
            while p < len(transferPath) - 1:
                openWell = transferPath[p + 1]
                currentWell = transferPath[p]
                closeWell = transferPath[p - 1]
                if p == 0 and len(self.mfWellConnections[closeWell]) == 1:
                    config['details'].append('o' + currentWell)
                    config['details'].append('o' + openWell)
                    config['details'].append('call wait' + waitNum)
                    global p
                    p = 1
                    openWell = transferPath[p + 1]
                    closeWell = transferPath[p - 1]
                config['details'].append('c' + closeWell)
                config['details'].append('o' + openWell)
                config['details'].append('call wait' + waitNum)
                if p == (len(transferPath) - 2) and len(self.mfWellConnections[openWell]) == 1:
                    config['details'].append('c' + currentWell)
                    config['details'].append('c' + openWell)
                    config['details'].append('call wait' + waitNum)
                p += 1
            config['details'].append('end')
            config['wait'] = ['wait' + waitNum, 'w' + str(wait), 'end']
            transfers.append(config)
        return transfers

    def saveTransfers(self, transferList):
        self.config('main')
        for name, times in ((t['name'], t['times']) for t in [transfer for transfer in transferList]):
            self.config('call ' + name + (' ' + str(times) if times > 1 else ''))
        self.config('end')
        self.config('')
        for transaction in (tr['details'] for tr in transferList):
            for line in transaction:
                self.config(line)
            self.config('')
        for wait in (tr['wait'] for tr in transferList):
            for line in wait:
                self.config(line)
            self.config('')


    def findPath(self, source, destination, path=[]):
        """
        Finds a shortest path between two wells on a microfluidic table.
        
        :param source: source well, int (must be in self.mfWellConnections)
        :param destination: destination well, int (must be in self.mfWellConnections)
        :param path: current path
        :return: resulting path, list

        """
        path = path + [source]
        if source == destination:
            return path
        if source not in self.mfWellConnections:
            return None
        shortestPath = None
        for node in self.mfWellConnections[source]:
            if node not in path:
                newPath = self.findPath(node, destination, path)
                if newPath:
                    if not shortestPath or len(newPath) < len(shortestPath):
                        shortestPath = newPath
        return shortestPath


    def parseCommand(self, transferList):
        print('transferList', transferList)
        trList = []
        for option in transferList:
            if option['command'] == 'message' or option['command'] == 'comment':
                trList.append(option)
                self.transactions.append(trList)


    def config(self, line):
        self.robotConfig.append(line)


    def saveConfig(self):
        fileName = 'esc' + os.sep + 'config' + self.expID + '.mf'
        open(fileName, 'w').close()
        myfile = open(fileName, 'a')
        for line in self.robotConfig:
            myfile.write(line.rstrip() + '\r\n')
        myfile.close()


    def log(self, item):
        from datetime import datetime

        time = str(datetime.now())
        self.logger.append(time + ': ' + item)


    def saveLog(self):
        logName = 'logs/experiment' + self.expID + '.log'
        self.log('Translation log location: ' + logName)
        writefile = open(logName, "a")
        writefile.writelines("%s\n" % item for item in self.logger)
        print('Translation log location: ' + logName)
        
        
class defaults:
    fileExtensions = {'mfp' : 'mf'}