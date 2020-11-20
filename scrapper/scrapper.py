import os
import re
import requests
import json
from bs4 import BeautifulSoup


class FrameDataScrapper:

    def __init__(self):
        self.characters = {'ehonda': {'vt1': None, 'vt2': None}}
        # self.characters = json.load(open('./config/characters.json'))
        self.url = 'https://game.capcom.com/cfn/sfv/character/{character}/frame/table/{stance}#vt{vt}'
        self.cookies = {
            'language': 'en',
            'vmail': '49',
            'consent_memory': 'eyJuIjoxLCJtIjoxLCJwIjoxLCJ0IjoxLCJvayI6MH0%3D',
        }
        self.inputs = json.load(open('./config/inputs.json'))

    @staticmethod
    def getFirstClass(element):
        return element.get('class', [None])[0]

    @staticmethod
    def getText(element):
        text = re.sub(r'\s{2,}', ' ', element.text.replace('\n', ' '))
        text = re.sub(r'\s{1,}$', '', text)
        text = re.sub(r'^\s{1,}', '', text)
        return text

    @staticmethod
    def tryRemove(file):
        try:
            os.remove(file)
        except:
            pass

    def pullFrameData(self, shouldUpdate=False):
        for character, sdata in self.characters.items():
            if(list(sdata.values())[0] == None):  # These are v-triggers
                for vt in sdata:
                    self.characters[character][vt] = self.pullFrameDataOfCharacter(
                        character, vt[2], shouldUpdate=shouldUpdate)
            else:  # It has also a stance
                for stance in sdata:
                    for vt in sdata[stance]:
                        self.characters[character][stance][vt] = self.pullFrameDataOfCharacter(
                            character, vt[2], stance=stance, shouldUpdate=shouldUpdate)

    def pullFrameDataOfCharacter(self, character, vt, stance=None, shouldUpdate=False):
        soup = self.loadSoup(character, vt, stance, shouldUpdate)
        tableHeaders = self.getTableHeaders(soup)
        for table in tableHeaders:
            data = self.getTableContent(soup, table[0])
            print(data)

        return 'pingo'

    def getTableHeaders(self, soup):
        rows = soup.find('table', {'class': 'frameTbl'}).findAll('tr')
        types = []
        for row in rows:
            headers = row.findAll('th')
            for header in headers:
                if(self.getFirstClass(header) == 'sep3'):
                    continue
                if(self.getFirstClass(header) == 'type'):
                    types.append([self.getText(header)])
                elif(header.text == 'Move Name'):
                    types[-1].extend(['Move Name', 'Move Input'])
                elif(header.text == 'Frame'):
                    types[-1].extend(['Frame_Startup',
                                      'Frame_Active', 'Frame_Recovery'])
                elif(header.text == 'Recovery'):
                    types[-1].extend(['Recovery_OnHit', 'Recovery_OnBlock'])
                elif(header.text == 'V-Trigger Cancel Recovery'):
                    types[-1].extend(['VT Cancel Recovery_OnHit',
                                      'VT Cancel Recovery_OnBlock'])
                else:
                    types[-1].append(self.getText(header))
        return list(map(lambda t: (t[0], t[1:]), types))

    def getTableContent(self, soup, table):
        rows = soup.find('table', {'class': 'frameTbl'}).findAll(['tr', 'th'])
        beginning = soup.find('th', text=table, attrs={'class': 'type'})
        if(beginning is None):
          beginning = soup.find('th', text=re.compile(
              table + r'\s*'), attrs={'class': 'type'})
        types = []
        range = False
        for row in rows:
            if(row == beginning):
                range = True
            if(row != beginning and self.getFirstClass(row) == 'type'):
                range = False
            headers = row.findAll('td')
            for header in headers:
              if(range == True):
                if(self.getFirstClass(header) == 'name'):
                  moveList = self.parseName(header)
                  types.append(moveList)
                elif(self.getFirstClass(header) == 'blank'):
                  types[-1].append(None)
                else:
                  try:
                    types[-1].append([])
                    for var in header:
                      types[-1][-1].append(self.getText(var))
                  except AttributeError:
                    types[-1].pop()
                    types[-1].append(self.getText(header))
        return types

    def parseName(self, moveChain):
        name = ""
        chain = []
        for child in moveChain:
            if(child.name == 'p' and self.getFirstClass(child) == 'name'):
                name = self.getText(child)
                if(child.find('span', {'class': 'vt'}) is not None):
                    name = 'V - ' + name[1:]
            elif(child.name == 'p'):
                span = child.find('span')
                chain.append(self.getFirstClass(span)[4:6])
            elif(child.name == 'span'):
                chain.append(self.getText(child))
            elif(child.name == 'img'):
                if(child['src'] not in self.inputs):
                    print('Agrega esta url:', child)
                    exit(0)
                chain.append(self.inputs[child['src']])
            else:
                chain.append(child)
        return [name, ' '.join(chain)]

    def loadSoup(self, character, vt, stance, shouldUpdate):
        path = f'./html/{character}-vt{vt}.html'
        if(stance):
            path = path[:-5]+f'-st{stance}'+path[-5:]
        if(shouldUpdate):
            self.tryRemove(path)
        if(os.path.exists(path)):
            return BeautifulSoup(open(path).read(), 'html.parser')
        else:
            url = self.url.replace(
                '{character}', character).replace('{vt}', vt).replace('{stance}', '' if stance is None else stance)
            print(url)
            if('scirid' not in self.cookies):
                print('Please provide a scirid: ', end='')
                self.cookies['scirid'] = re.sub(r'\s', '', input())
            page = requests.get(url, cookies=self.cookies)
            if(page.status_code != 200):
                print('Received status code', page.status_code)
                print('Check the scirid token')
                exit(-1)
            with open(path, 'w+') as f:
                f.write(page.text)
            return BeautifulSoup(page.text, 'html.parser')


framedataScrapper = FrameDataScrapper()
framedataScrapper.pullFrameData()
