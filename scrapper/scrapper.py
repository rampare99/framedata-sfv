import os
import re
import requests
from bs4 import BeautifulSoup


def remove_empty(l):
    return tuple(filter(lambda x: not isinstance(x, (list)) or x, (remove_empty(x) if isinstance(x, (tuple, list)) else x for x in l)))


class FrameDataScrapper:

    def __init__(self):
        self.characters = ['ehonda']
        self.url = 'https://game.capcom.com/cfn/sfv/character/{character}/frame/table#vt{vt}'
        self.cookies = {
            'language': 'en',
            'vmail': '49',
            'consent_memory': 'eyJuIjoxLCJtIjoxLCJwIjoxLCJ0IjoxLCJvayI6MH0%3D',
        }
        self.framedata = {}
        self.inputs = {
            "https://game.capcom.com/cfn/sfv/as/img/cmd/btn/punch.gif?h=cdde7fc8901adab4686621a896922c1a": 'P',
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/236.gif?h=81e527af198d2e5ddacf0aed44f61cdb": '236',
            "https://game.capcom.com/cfn/sfv/as/img/cmd/btn/kick.gif?h=782ca1c7f3e42332887e30ab0a5d37df": "K",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/63214.gif?h=94b63ab09919622f1e451e21ffa32412": "63214",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/623.gif?h=91ce5a17eb810540f177449f580dc244": "623",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/3.gif?h=705de611ba081ecabe11861b0c4047f3": "3",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/2.gif?h=146d9a7c6b006b57d999d5633df090f0": "2",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/next.gif?h=124a6dc32d24b2472cf317a685310f07": ">",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/4.gif?h=30f455943bd68bafe11e9359b871465d": "4",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/6.gif?h=24d3886f118640b674eae14fabd0e016": "6",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/5.gif?h=5c61278719e2dea3e98b59650f7f9a29": "5",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/c4.gif?h=2a138cf782017000f8c40c9f6013b2e3": "C4",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/c2.gif?h=7658c782425aef8b1eb937fcc509e195": "C2",
            "https://game.capcom.com/cfn/sfv/as/img/cmd/key/8.gif?h=9247962a975feda8fd5e99965f18f774": "8",
        }

    @staticmethod
    def getFirstClass(element):
        return element.get('class', [None])[0]

    @staticmethod
    def getText(element):
        text = re.sub(r'\s{2,}', ' ', element.text.replace('\n', ' '))
        text = re.sub(r'\s{1,}$', '', text)
        text = re.sub(r'^\s{1,}', '', text)
        return text

    def pullFrameData(self, shouldUpdate=False):
        for character in self.characters:
            for vt in ['1', '2']:
                if(shouldUpdate):
                    try:
                        os.remove(f'./html/{character}-{vt}.html')
                    except:
                        pass
                self.framedata[character] = self.pullFrameDataOfCharacter(
                    character, vt)

    def pullFrameDataOfCharacter(self, character, vt):
        soup = self.loadSoup(character, vt)
        tableHeaders = self.getTableHeaders(soup)
        #print(tableHeaders)
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
          beginning = soup.find('th', text=re.compile(table + r'\s*'), attrs={'class': 'type'})
        print(table)
        types = []
        range = False
        for row in rows:
            if(row == beginning):
                range = True
            if(row != beginning and self.getFirstClass(row) == 'type'):
                range = False
            headers = row.findAll('td')
            for header in headers:
              if(range==True):
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

    def loadSoup(self, character, vt):
        if(os.path.exists(f'./html/{character}-{vt}.html')):
            return BeautifulSoup(open(f'./html/{character}-{vt}.html').read(), 'html.parser')
        else:
            url = self.url.replace(
                '{character}', character).replace('{vt}', vt)
            if('scirid' not in self.cookies):
                print('Please provide a scirid: ', end='')
                self.cookies['scirid'] = re.sub(r'\s', '', input())
            page = requests.get(url, cookies=self.cookies)
            if(page.status_code != 200):
                print('Received status code', page.status_code)
                print('Check the scirid token')
                exit(-1)
            with open(f'html/{character}-{vt}.html', 'w+') as f:
                f.write(page.text)
            return BeautifulSoup(page.text, 'html.parser')


framedataScrapper = FrameDataScrapper()
framedataScrapper.pullFrameData()