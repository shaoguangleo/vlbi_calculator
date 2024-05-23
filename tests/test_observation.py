import pytest
import numpy as np
from vlbiplanobs import observation as obs
# from vlbiplanobs import stations
from astropy import coordinates as coord
from astropy import units as u
from astropy.time import Time
from rich import print as rprint




def test_polarizations():
    assert obs.Polarization.SINGLE == obs.Polarization(1)
    assert obs.Polarization.SINGLE == obs.Polarization['SINGLE']
    assert obs.Polarization.DUAL == obs.Polarization(2)
    assert obs.Polarization.DUAL == obs.Polarization['DUAL']
    assert obs.Polarization.FULL == obs.Polarization(4)
    assert obs.Polarization.FULL == obs.Polarization['FULL']


def test_observation_init():
    o = obs.Observation()
    o.polarizations = 'dual'
    assert o.polarizations.value == 2
    o.polarizations = 4
    assert o.polarizations == obs.Polarization.FULL


    for tar_name, tar_coord in (('Target', '10h58m29.6s +81d33m58.8s'),
                    (['Tar1', 'Tar2'], ['10h58m29.6s +81d33m58.8s', '20h58m29.6s +71d33m58.8s'])):
        target = obs.Source(tar_name, tar_coord)
        o = obs.Observation(target=target)
        o.times = Time('2020-06-15 20:00', scale='utc') + np.arange(0, 720, 10)*u.min
        o.band = '18'
        o.datarate = 1024
        o.subbands = 8
        o.channels = 32
        o.polarizations = 2
        o.polarizations = 'full'
        with pytest.raises(ValueError):
            o.polarizations = 0
            o.polarizations = -5
            o.polarizations = 'efww'
            o.polarizations = ''
            o.polarizations = None

        o.inttime = 2

        assert len(o.target) == len(tar_name) if isinstance(tar_name, list) else 1
        # all_stations = stations.Network.get_stations_from_configfile()
        evn6 = ['Ef', 'Jb2', 'On', 'Hh', 'T6', 'Wb', 'Sv', 'Zc', 'Pa', 'Mp', 'Ho', 'Nl', 'Pt', 'Sc', 'Kp', 'Hn']
        o.stations_from_codenames(evn6)
        _ = o.elevations()
        temp = o.is_visible()
        assert len(temp) == len(evn6) and len(evn6) == len(o.stations)
        # If multiple sources, then it will keep the structure of one ouput per source
        assert temp[evn6[0]].shape[0] == len(tar_name) if isinstance(tar_name, list) else 1
        # temp = o.guest_times_for_source()
        # beam = o.synthesized_beam)
        # _ = o.thermal_noise()
        # _ = o.get_uv_array()
        # _ = o.get_dirtymap(robust='natural')
        # _ = o.get_dirtymap(robust='uniform')
        # fig, ax = plt.subplots()

        # If no time is defined
        o.times = None
        o.is_visible()


