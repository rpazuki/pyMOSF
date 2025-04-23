from setuptools import setup

if __name__ == "__main__":
    # # Detect which extras are being installed
    # install_kivy = any('kivy' in arg for arg in sys.argv)
    # install_beeware = any('beeware' in arg for arg in sys.argv)

    # # Base packages that are always included
    # packages = find_packages(include=['pyMOSF',
    #                                   'pyMOSF.config*',
    #                                   'pyMOSF.services*',
    #                                   'pyMOSF.core*'])

    # # Add framework-specific packages based on extras
    # if install_kivy:
    #     packages.extend(find_packages(include=['pyMOSF.kivy*']))
    # if install_beeware:
    #     packages.extend(find_packages(include=['pyMOSF.toga*']))

    # # Override the packages option from setup.cfg
    # setup(packages=packages)
    setup()
