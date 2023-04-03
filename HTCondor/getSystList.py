def getSystList(config):
    systList = []
    for line in open(config):
        lineStrip = line.split('%')[0].strip()
        if lineStrip.startswith('#'):
            continue
        if 'Systematic:' in lineStrip:
            syst_line = lineStrip.split(":")[1].strip()

            # Split the systematic names by semicolon and add them to the systList
            for syst in syst_line.split(';'):
                syst = syst.strip()  # Remove any spaces before and after the systematic name
                
                # Check if the systematic names are enclosed by double quotes
                if syst.startswith('"') and syst.endswith('"'):
                    syst = syst[1:-1]  # Remove the double quotes

                print(syst)

getSystList("config_1l_baseline_BONLY.yaml")