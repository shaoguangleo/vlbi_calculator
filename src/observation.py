
"""Defines an observation with given network(s), a target source,
time range and the observing band.
"""

import numpy as np
from astropy.time import Time
from astropy import coordinates as coord
from astropy import units as u
from astroplan import FixedTarget

from . import stations


class Source(FixedTarget):
    """Defines a source with some coordinates and a name.
    Inputs
        - coordinates : str
            In a format recognized by astropy.coordinates.SkyCoord
            (e.g. XXhXXmXXs XXdXXmXXs)
        - name : str (optional)
            Name associated to the source
    """
    def __init__(self, coordinates, name=None):
        super().__init__(coord.SkyCoord(coordinates), name)


class Observation(object):
    def __init__(self, target=None, times=None, band=None, datarate=None,subbands=None,
                channels=None, polarizations=None, inttime=None, ontarget=1.0,
                stations=None, bits=2):
        if target is not None:
            self.target = target
        if times is not None:
            self.times = times
        if band is not None:
            self.band = band
        if datarate is not None:
            self.datarate = datarate
        if subbands is not None:
            self.subbands = subbands
        if channels is not None:
            self.channels = channels
        if polarizations is not None:
            self.polarizations = polarizations
        if inttime is not None:
            self.inttime = inttime
        if stations is not None:
            self.stations = stations

        self.bitsampling = bits
        self.ontarget_fraction = ontarget


    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, new_target):
        assert isinstance(new_target, Source)
        self._target = new_target
        # TODO: update the elevation...

    @property
    def times(self):
        return self._times

    @times.setter
    def times(self, new_times):
        assert isinstance(new_times, Time)
        self._times = new_times
        self._gstimes = self._times.sidereal_time('mean', 'greenwich')

    @property
    def gstimes(self):
        return self._gstimes

    @property
    def band(self):
        return self._band

    @band.setter
    def band(self, new_band):
        self._band = new_band

    @property
    def wavelength(self):
        """Returns the central wavelength of the observations with units
        """
        return float(self.band.replace('cm',''))*u.cm

    @property
    def frequency(self):
        """Returns the central frequency of the observations with units
        """
        return 30*u.GHz/self.wavelength.to(u.cm).value

    @property
    def datarate(self):
        """Datarate in Mbps
        """
        return self._datarate

    @datarate.setter
    def datarate(self, new_datarate):
        """If no units provided, Mbps assumed.
        """
        if isinstance(new_datarate, int):
            self._datarate = new_datarate*u.Mbit/u.s
        elif isinstance(new_datarate, u.Quantity):
            self._datarate = new_datarate.to(u.Mbit/u.s)
        else:
            raise ValueError(f"Unknown type for {new_datarate} (int/Quantity(bit/s) expected)")

    @property
    def subbands(self):
        return self._subbands

    @subbands.setter
    def subbands(self, n_subbands):
        assert isinstance(n_subbands, int)
        self._subbands = n_subbands

    @property
    def channels(self):
        return self._channels

    @channels.setter
    def channels(self, n_channels):
        assert isinstance(n_channels, int)
        self._channels = n_channels

    @property
    def polarizations(self):
        return self._polarizations

    @polarizations.setter
    def polarizations(self, n_pols):
        assert n_pols in (1, 2, 4)
        self._polarizations = n_pols

    @property
    def inttime(self):
        """Integration time during the observation.
        """
        return self._inttime

    @inttime.setter
    def inttime(self, new_inttime):
        if isinstance(new_inttime, float) or isinstance(new_inttime, int):
            self._inttime = new_inttime*u.s
        elif isinstance(new_inttime, u.Quantity):
            self._inttime = new_inttime.to(u.s)
        else:
            raise ValueError(f"Unknown type for {new_inttime} (float/int/Quantity(s) expected)")

    @property
    def ontarget_fraction(self):
        """Fraction of the total observing time spent on the target source
        """
        return self._ontarget

    @ontarget_fraction.setter
    def ontarget_fraction(self, ontarget):
        assert 0.0 < ontarget <= 1.0
        self._ontarget = ontarget

    @property
    def bandwidth(self):
        """Returns the total bandwidth of the observation.
        """
        pols = self.polarizations % 3 + self.polarizations // 3  # Either 1 or 2
        return (self.datarate/(pols*self.bitsampling*2)).to(u.MHz)

    @property
    def bitsampling(self):
        return self._bitsampling

    @bitsampling.setter
    def bitsampling(self, new_bitsampling):
        if isinstance(new_bitsampling, float) or isinstance(new_bitsampling, int):
            self._bitsampling = new_bitsampling*u.bit
        elif isinstance(new_inttime, u.Quantity):
            self._bitsampling = new_bitsampling.to(u.bit)
        else:
            raise ValueError(f"Unknown type for {new_bitsampling} (float/int/Quantity(bit) expected)")

    @property
    def stations(self):
        return self._stations

    @stations.setter
    def stations(self, new_stations):
        assert isinstance(new_stations, stations.Stations)
        self._stations = new_stations
        # TODO: update elevation


    def elevations(self):
        """Returns the target elevations for all stations along the observation.
        """
        elevations = {}
        for a_station in self.stations:
            elevations[a_station.codename] = a_station.elevation(self.times, self.target)
        return elevations

    def altaz(self):
        """Returns the target altaz for all stations along the observation.
        """
        aa = {}
        for a_station in self.stations:
            aa[a_station.codename] = a_station.altaz(self.times, self.target)
        return aa

    def is_visible(self):
        """Returns when the target is visible for all stations for each time in the observation.
        """
        iv = {}
        for a_station in self.stations:
            iv[a_station.codename] = a_station.is_visible(self.times, self.target)
        return iv

    def longest_baseline(self):
        """Returns the longest baseline in the observation.
        It retuns the tuple ((ant1,ant2), length)
        where `ant1,ant2` are the antennas in such baseline, and `length` its length.
        """
        # TODO: To Implement
        return ('XX','XX'), 1000*u.km
        raise NotImplemented('observation.longest_baseline')

    def bandwidth_smearing(self):
        """Returns the bandwidth smearing expected for the given observation.
        """
        # TODO: Check if with units it works
        return ((49500*u.arcsec*u.MHz*u.km)*self.channels/ \
            (self.longest_baseline()[1]*self.bandwidth)).to(u.arcsec)

    def time_smearing(self):
        """Returns the time smearing expected for the given observation.
        """
        # TODO: Check if with units it works
        return ((18560*u.arcsec*u.km*u.s/u.cm)*\
                (self.wavelength/self.longest_baseline()[1])/self.inttime).to(u.arcsec)

    def datasize(self):
        """Returns the expected size for the output FITS files.
        """
        temp = len(self.stations)**2*(self.times[-1]-self.times[0])/self.inttime
        temp *= self.polarizations*self.subbands*self.channels
        temp *= 1.75*u.GB/(131072*3600)
        return temp.to(u.GB)


    def thermal_noise(self):
        """Returns the expected thermal noise for the given observation
        """
        main_matrix = np.zeros((len(self.times), len(self.stations)))
        visible = self.is_visible()
        for i,stat in enumerate(self.stations):
            main_matrix[:,i][visible[stat.codename]] = stat.sefd(self.band)
        # For each timestamp
        # Determines the noise level for each time stamp.
        temp = 0.0
        for i,ti in enumerate(main_matrix[:-1]):
            sefds = ti[np.where(ti > 0.0)]
            for j in range(len(sefds)):
                for k in range(j+1, len(sefds)):
                    temp += (self.times[i+1]-self.times[i]).to(u.s).value/(sefds[j]*sefds[k])

        temp = 1.0/np.sqrt(temp*self.ontarget_fraction)
        # TODO: fix units problem.
        return ((1.0/0.7)*temp/np.sqrt(self.datarate.to(u.bit/u.s).value/2))*u.Jy

    # def _get_baseline_numbers(self):
    #     """Returns the (int) number corresponding to the each baseline.
    #     It basically transforms each baseline in the array to a int number:
    #         (0,1), (0,2), ... (0, N), (1, 2),... --> 1, 2, ..., N, N+1, ...
    #     Inputs:
    #         - ant1, ant2 : str
    #             The codename of each antenna in the baseline
    #     Returns:
    #         - dict { 'Ant1Ant2': int,... } where Ant1Ant2 is a str composite of
    #                 the two antena codenames.
    #     """
    #     statcodes = [s.codename for s in self.stations]
    #     d = {}
    #     for i,si in enumerate(statcodes):
    #         for j in range(i+1, len(statcodes)):
    #             d[si+statcodes[j]] =
    #
    # def _get_baseline_number(self, ant1, ant2):
    #     """Returns the (int) number corresponding to the given baseline.
    #     It basically transforms each baseline in the array to a int number:
    #         (0,1), (0,2), ... (0, N), (1, 2),... --> 1, 2, ..., N, N+1, ...
    #     Inputs:
    #         - ant1, ant2 : str
    #             The codename of each antenna in the baseline
    #     Returns int.
    #     """
    #     statcodes = [s.codename for s in self.stations]
    #     for i,si in enumerate(statcodes):
    #         for j in range(i+1, len(statcodes)):


    def get_uv(self):
        """Returns the uvw values for each baseline and each timestamp.
        It returns a list with the two antenna codes and the uvw values in meters.
        """
        hourangle = self.target.ra.to(u.hourangle) - self.gstimes
        nstat = len(self.stations)
        # Determines the xyz of all baselines. Time independent
        bl_xyz = np.empty(((nstat*(nstat-1))//2, 3))
        s = [ant.location for ant in self.stations]
        for i in range(nstat):
            for j in range(i+1, nstat):
                # An unique number defining a baseline
                k = int( i*(nstat-1) - sum(range(i)) + j-i )
                bl_xyz[k-1,:] = np.array([ii.value for ii in s[i].to_geocentric()]) - \
                             np.array([ii.value for ii in s[j].to_geocentric()])

        # Matrix to convert xyz to uvw for each timestamp (w is not considered)
        m = np.array([[np.sin(hourangle), np.cos(hourangle), np.zeros(len(hourangle))],
                      [-np.sin(self.target.dec)*np.cos(hourangle),
                      np.sin(self.target.dec)*np.sin(hourangle),
                      np.cos(self.target.dec)*np.ones(len(hourangle))]])

        return m @ bl_xyz

