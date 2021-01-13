framedataScrapper = FrameDataScrapper()
framedata = framedataScrapper.pullFrameData()

pingo=[
    'Move Name', 'Move Input', 'Startup', 'Active', 'Recovery', 'On Hit', 'On Block',
    'VT On Hit', 'VT On Block', 'Cancel Info', 'Damage', 'Stun',
    'Meter Gain (Whiff/Hit)', 'Properties', 'Projectile Nullification',
    'Airborne Hurtbox', 'Comments']

frames = []

for header in framedata[0]:
    frames.append(pd.DataFrame(header, columns=pingo))

for header in framedata[1]:
    frames.append(pd.DataFrame(header, columns=pingo))

result = pd.concat(frames)
result.to_csv(r'/home/ramiro/proyectos/framedata-sfv/scrapper/ehonda.csv', index = False)

print(result)
