#!/usr/bin/env python3
#
#    MIT License
#
#    Copyright (c) 2019 Don Cross <cosinekitty@gmail.com>
#
#    Permission is hereby granted, free of charge, to any person obtaining a copy
#    of this software and associated documentation files (the "Software"), to deal
#    in the Software without restriction, including without limitation the rights
#    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the Software is
#    furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in all
#    copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#    SOFTWARE.
#
"""Astronomy Engine by Don Cross

See the GitHub project page for full documentation, examples,
and other information:

https://github.com/cosinekitty/astronomy

"""

import math
import datetime
import enum

_PI2 = 2.0 * math.pi
_EPOCH = datetime.datetime(2000, 1, 1, 12)
_T0 = 2451545.0
_MJD_BASIS = 2400000.5
_Y2000_IN_MJD = _T0 - _MJD_BASIS
_ASEC360 = 1296000.0
_ASEC2RAD = 4.848136811095359935899141e-6
_ARC = 3600.0 * 180.0 / math.pi     # arcseconds per radian
_C_AUDAY = 173.1446326846693        # speed of light in AU/day
_ERAD = 6378136.6                   # mean earth radius in meters
_AU = 1.4959787069098932e+11        # astronomical unit in meters
_KM_PER_AU = 1.4959787069098932e+8
_ANGVEL = 7.2921150e-5
_SECONDS_PER_DAY = 24.0 * 3600.0
_SOLAR_DAYS_PER_SIDEREAL_DAY = 0.9972695717592592
_MEAN_SYNODIC_MONTH = 29.530588
_EARTH_ORBITAL_PERIOD = 365.256
_REFRACTION_NEAR_HORIZON = 34.0 / 60.0
_SUN_RADIUS_AU  = 4.6505e-3
_MOON_RADIUS_AU = 1.15717e-5
_ASEC180 = 180.0 * 60.0 * 60.0
_AU_PER_PARSEC = _ASEC180 / math.pi

def _LongitudeOffset(diff):
    offset = diff
    while offset <= -180.0:
        offset += 360.0
    while offset > 180.0:
        offset -= 360.0
    return offset

def _NormalizeLongitude(lon):
    while lon < 0.0:
        lon += 360.0
    while lon >= 360.0:
        lon -= 360.0
    return lon

class Vector:
    """A Cartesian vector with 3 space coordinates and 1 time coordinate.

    The vector's space coordinates are measured in astronomical units (AU).
    The coordinate system varies and depends on context.
    The vector also includes a time stamp.

    Attributes
    ----------
    x : float
        The x-coordinate of the vector, measured in AU.
    y : float
        The y-coordinate of the vector, measured in AU.
    z : float
        The z-coordinate of the vector, measured in AU.
    t : Time
        The date and time at which the coordinate is valid.
    """
    def __init__(self, x, y, z, t):
        self.x = x
        self.y = y
        self.z = z
        self.t = t

    def Length(self):
        """Returns the length of the vector in AU."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

@enum.unique
class Body(enum.IntEnum):
    """The celestial bodies supported by Astronomy Engine calculations.

    Values
    ------
    Invalid: An unknown, invalid, or undefined celestial body.
    Mercury: The planet Mercury.
    Venus: The planet Venus.
    Earth: The planet Earth.
    Mars: The planet Mars.
    Jupiter: The planet Jupiter.
    Saturn: The planet Saturn.
    Uranus: The planet Uranus.
    Neptune: The planet Neptune.
    Pluto: The planet Pluto.
    Sun: The Sun.
    Moon: The Earth's moon.
    """
    Invalid = -1
    Mercury = 0
    Venus = 1
    Earth = 2
    Mars = 3
    Jupiter = 4
    Saturn = 5
    Uranus = 6
    Neptune = 7
    Pluto = 8
    Sun = 9
    Moon = 10

def BodyCode(name):
    """Finds the Body enumeration value, given the name of a body.

    Parameters
    ----------
    name: str
        The common English name of a supported celestial body.

    Returns
    -------
    #Body
        If `name` is a valid body name, returns the enumeration
        value associated with that body.
        Otherwise, returns `Body.Invalid`.

    Example
    -------

    >>> astronomy.BodyCode('Mars')
    <Body.Mars: 3>

    """
    if name not in Body.__members__:
        return Body.Invalid
    return Body[name]

def _IsSuperiorPlanet(body):
    return body in [Body.Mars, Body.Jupiter, Body.Saturn, Body.Uranus, Body.Neptune, Body.Pluto]

_PlanetOrbitalPeriod = [
    87.969,
    224.701,
    _EARTH_ORBITAL_PERIOD,
    686.980,
    4332.589,
    10759.22,
    30685.4,
    60189.0,
    90560.0
]

class Error(Exception):
    """Indicates an error in an astronomical calculation."""
    def __init__(self, message):
        Exception.__init__(self, message)

class EarthNotAllowedError(Error):
    """The Earth is not allowed as the celestial body in this calculation."""
    def __init__(self):
        Error.__init__(self, 'The Earth is not allowed as the body.')

class InvalidBodyError(Error):
    """The celestial body is not allowed for this calculation."""
    def __init__(self):
        Error.__init__(self, 'Invalid astronomical body.')

class BadVectorError(Error):
    """A vector magnitude is too small to have a direction in space."""
    def __init__(self):
        Error.__init__(self, 'Vector is too small to have a direction.')

class InternalError(Error):
    """An internal error occured that should be reported as a bug.

    Indicates an unexpected and unrecoverable condition occurred.
    If you encounter this error using Astronomy Engine, it would be very
    helpful to report it at the [Issues](https://github.com/cosinekitty/astronomy/issues)
    page on GitHub. Please include a copy of the stack trace, along with a description
    of how to reproduce the error. This will help improve the quality of
    Astronomy Engine for everyone! (Thank you in advance from the author.)
    """
    def __init__(self):
        Error.__init__(self, 'Internal error - please report issue at https://github.com/cosinekitty/astronomy/issues')

class NoConvergeError(Error):
    """A numeric solver did not converge.

    Indicates that there was a failure of a numeric solver to converge.
    If you encounter this error using Astronomy Engine, it would be very
    helpful to report it at the [Issues](https://github.com/cosinekitty/astronomy/issues)
    page on GitHub. Please include a copy of the stack trace, along with a description
    of how to reproduce the error. This will help improve the quality of
    Astronomy Engine for everyone! (Thank you in advance from the author.)
    """
    def __init__(self):
        Error.__init__(self, 'Numeric solver did not converge - please report issue at https://github.com/cosinekitty/astronomy/issues')

def _SynodicPeriod(body):
    if body == Body.Earth:
        raise EarthNotAllowedError()
    if body < 0 or body >= len(_PlanetOrbitalPeriod):
        raise InvalidBodyError()
    if body == Body.Moon:
        return _MEAN_SYNODIC_MONTH
    return abs(_EARTH_ORBITAL_PERIOD / (_EARTH_ORBITAL_PERIOD/_PlanetOrbitalPeriod[body] - 1.0))

def _AngleBetween(a, b):
    r = a.Length() * b.Length()
    if r < 1.0e-8:
        return BadVectorError()
    dot = (a.x*b.x + a.y*b.y + a.z*b.z) / r
    if dot <= -1.0:
        return 180.0
    if dot >= +1.0:
        return 0.0
    return math.degrees(math.acos(dot))

class _delta_t_entry_t:
    def __init__(self, mjd, dt):
        self.mjd = mjd
        self.dt = dt

_DT = [
_delta_t_entry_t(-72638.0, 38),
_delta_t_entry_t(-65333.0, 26),
_delta_t_entry_t(-58028.0, 21),
_delta_t_entry_t(-50724.0, 21.1),
_delta_t_entry_t(-43419.0, 13.5),
_delta_t_entry_t(-39766.0, 13.7),
_delta_t_entry_t(-36114.0, 14.8),
_delta_t_entry_t(-32461.0, 15.7),
_delta_t_entry_t(-28809.0, 15.6),
_delta_t_entry_t(-25156.0, 13.3),
_delta_t_entry_t(-21504.0, 12.6),
_delta_t_entry_t(-17852.0, 11.2),
_delta_t_entry_t(-14200.0, 11.13),
_delta_t_entry_t(-10547.0, 7.95),
_delta_t_entry_t(-6895.0, 6.22),
_delta_t_entry_t(-3242.0, 6.55),
_delta_t_entry_t(-1416.0, 7.26),
_delta_t_entry_t(410.0, 7.35),
_delta_t_entry_t(2237.0, 5.92),
_delta_t_entry_t(4063.0, 1.04),
_delta_t_entry_t(5889.0, -3.19),
_delta_t_entry_t(7715.0, -5.36),
_delta_t_entry_t(9542.0, -5.74),
_delta_t_entry_t(11368.0, -5.86),
_delta_t_entry_t(13194.0, -6.41),
_delta_t_entry_t(15020.0, -2.70),
_delta_t_entry_t(16846.0, 3.92),
_delta_t_entry_t(18672.0, 10.38),
_delta_t_entry_t(20498.0, 17.19),
_delta_t_entry_t(22324.0, 21.41),
_delta_t_entry_t(24151.0, 23.63),
_delta_t_entry_t(25977.0, 24.02),
_delta_t_entry_t(27803.0, 23.91),
_delta_t_entry_t(29629.0, 24.35),
_delta_t_entry_t(31456.0, 26.76),
_delta_t_entry_t(33282.0, 29.15),
_delta_t_entry_t(35108.0, 31.07),
_delta_t_entry_t(36934.0, 33.150),
_delta_t_entry_t(38761.0, 35.738),
_delta_t_entry_t(40587.0, 40.182),
_delta_t_entry_t(42413.0, 45.477),
_delta_t_entry_t(44239.0, 50.540),
_delta_t_entry_t(44605.0, 51.3808),
_delta_t_entry_t(44970.0, 52.1668),
_delta_t_entry_t(45335.0, 52.9565),
_delta_t_entry_t(45700.0, 53.7882),
_delta_t_entry_t(46066.0, 54.3427),
_delta_t_entry_t(46431.0, 54.8712),
_delta_t_entry_t(46796.0, 55.3222),
_delta_t_entry_t(47161.0, 55.8197),
_delta_t_entry_t(47527.0, 56.3000),
_delta_t_entry_t(47892.0, 56.8553),
_delta_t_entry_t(48257.0, 57.5653),
_delta_t_entry_t(48622.0, 58.3092),
_delta_t_entry_t(48988.0, 59.1218),
_delta_t_entry_t(49353.0, 59.9845),
_delta_t_entry_t(49718.0, 60.7853),
_delta_t_entry_t(50083.0, 61.6287),
_delta_t_entry_t(50449.0, 62.2950),
_delta_t_entry_t(50814.0, 62.9659),
_delta_t_entry_t(51179.0, 63.4673),
_delta_t_entry_t(51544.0, 63.8285),
_delta_t_entry_t(51910.0, 64.0908),
_delta_t_entry_t(52275.0, 64.2998),
_delta_t_entry_t(52640.0, 64.4734),
_delta_t_entry_t(53005.0, 64.5736),
_delta_t_entry_t(53371.0, 64.6876),
_delta_t_entry_t(53736.0, 64.8452),
_delta_t_entry_t(54101.0, 65.1464),
_delta_t_entry_t(54466.0, 65.4573),
_delta_t_entry_t(54832.0, 65.7768),
_delta_t_entry_t(55197.0, 66.0699),
_delta_t_entry_t(55562.0, 66.3246),
_delta_t_entry_t(55927.0, 66.6030),
_delta_t_entry_t(56293.0, 66.9069),
_delta_t_entry_t(56658.0, 67.2810),
_delta_t_entry_t(57023.0, 67.6439),
_delta_t_entry_t(57388.0, 68.1024),
_delta_t_entry_t(57754.0, 68.5927),
_delta_t_entry_t(58119.0, 68.9676),
_delta_t_entry_t(58484.0, 69.2201),
_delta_t_entry_t(58849.0, 69.87),
_delta_t_entry_t(59214.0, 70.39),
_delta_t_entry_t(59580.0, 70.91),
_delta_t_entry_t(59945.0, 71.40),
_delta_t_entry_t(60310.0, 71.88),
_delta_t_entry_t(60675.0, 72.36),
_delta_t_entry_t(61041.0, 72.83),
_delta_t_entry_t(61406.0, 73.32),
_delta_t_entry_t(61680.0, 73.66)
]

def _DeltaT(mjd):
    if mjd <= _DT[0].mjd:
        return _DT[0].dt
    if mjd >= _DT[-1].mjd:
        return _DT[-1].dt
    # Do a binary search to find the pair of indexes this mjd lies between.
    lo = 0
    hi = len(_DT) - 2   # Make sure there is always an array element after the one we are looking at.
    while True:
        if lo > hi:
            # This should never happen unless there is a bug in the binary search.
            raise Error('Could not find delta-t value.')
        c = (lo + hi) // 2
        if mjd < _DT[c].mjd:
            hi = c-1
        elif mjd > _DT[c+1].mjd:
            lo = c+1
        else:
            frac = (mjd - _DT[c].mjd) / (_DT[c+1].mjd - _DT[c].mjd)
            return _DT[c].dt + frac*(_DT[c+1].dt - _DT[c].dt)

def _TerrestrialTime(ut):
    return ut + _DeltaT(ut + _Y2000_IN_MJD) / 86400.0

class Time:
    """Represents a date and time used for performing astronomy calculations.

    All calculations performed by Astronomy Engine are based on
    dates and times represented by `Time` objects.

    Parameters
    ----------
    ut : float
        UT1/UTC number of days since noon on January 1, 2000.
        See the `ut` attribute of this class for more details.

    Attributes
    ----------
    ut : float
        The floating point number of days of Universal Time since noon UTC January 1, 2000.
        Astronomy Engine approximates UTC and UT1 as being the same thing, although they are
        not exactly equivalent; UTC and UT1 can disagree by up to 0.9 seconds.
        This approximation is sufficient for the accuracy requirements of Astronomy Engine.
        Universal Time Coordinate (UTC) is the international standard for legal and civil
        timekeeping and replaces the older Greenwich Mean Time (GMT) standard.
        UTC is kept in sync with unpredictable observed changes in the Earth's rotation
        by occasionally adding leap seconds as needed.
        UT1 is an idealized time scale based on observed rotation of the Earth, which
        gradually slows down in an unpredictable way over time, due to tidal drag by the Moon and Sun,
        large scale weather events like hurricanes, and internal seismic and convection effects.
        Conceptually, UT1 drifts from atomic time continuously and erratically, whereas UTC
        is adjusted by a scheduled whole number of leap seconds as needed.
        The value in `ut` is appropriate for any calculation involving the Earth's rotation,
        such as calculating rise/set times, culumination, and anything involving apparent
        sidereal time.
        Before the era of atomic timekeeping, days based on the Earth's rotation
        were often known as *mean solar days*.
    tt : float
        Terrestrial Time days since noon on January 1, 2000.
        Terrestrial Time is an atomic time scale defined as a number of days since noon on January 1, 2000.
        In this system, days are not based on Earth rotations, but instead by
        the number of elapsed [SI seconds](https://physics.nist.gov/cuu/Units/second.html)
        divided by 86400. Unlike `ut`, `tt` increases uniformly without adjustments
        for changes in the Earth's rotation.
        The value in `tt` is used for calculations of movements not involving the Earth's rotation,
        such as the orbits of planets around the Sun, or the Moon around the Earth.
        Historically, Terrestrial Time has also been known by the term *Ephemeris Time* (ET).
    """
    def __init__(self, ut):
        self.ut = ut
        self.tt = _TerrestrialTime(ut)
        self.etilt = None

    @staticmethod
    def Make(year, month, day, hour, minute, second):
        """Creates a #Time object from a UTC calendar date and time.

        Parameters
        ----------
        year : int
            The UTC 4-digit year value, e.g. 2019.
        month : int
            The UTC month in the range 1..12.
        day : int
            The UTC day of the month, in the range 1..31.
        hour : int
            The UTC hour, in the range 0..23.
        minute : int
            The UTC minute, in the range 0..59.
        second : float
            The real-valued UTC second, in the range [0, 60).

        Returns
        -------
        #Time
        """
        micro = round(math.fmod(second, 1.0) * 1000000)
        second = math.floor(second - micro/1000000)
        d = datetime.datetime(year, month, day, hour, minute, second, micro)
        ut = (d - _EPOCH).total_seconds() / 86400
        return Time(ut)

    @staticmethod
    def Now():
        """Returns the computer's current date and time in the form of a #Time object.

        Uses the computer's system clock to find the current UTC date and time.
        Converts that date and time to a #Time value and returns the result.
        Callers can pass this value to other Astronomy Engine functions to
        calculate current observational conditions.

        Returns
        -------
        #Time
        """
        ut = (datetime.datetime.utcnow() - _EPOCH).total_seconds() / 86400.0
        return Time(ut)

    def AddDays(self, days):
        """Calculates the sum or difference of a #Time with a specified real-valued number of days.

        Sometimes we need to adjust a given #Time value by a certain amount of time.
        This function adds the given real number of days in `days` to the date and time
        in the calling object.

        More precisely, the result's Universal Time field `ut` is exactly adjusted by `days`
        and the Terrestrial Time field `tt` is adjusted correctly for the resulting UTC date and time,
        according to the historical and predictive Delta-T model provided by the
        [United States Naval Observatory](http://maia.usno.navy.mil/ser7/).

        The value of the calling object is not modified. This function creates a brand new
        #Time object and returns it.

        Parameters
        ----------
        days : float
            A floating point number of days by which to adjust `time`.
            May be negative, 0, or positive.

        Returns
        -------
        #Time
        """
        return Time(self.ut + days)

    def __str__(self):
        millis = round(self.ut * 86400000.0)
        n = _EPOCH + datetime.timedelta(milliseconds=millis)
        return '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:03d}Z'.format(n.year, n.month, n.day, n.hour, n.minute, n.second, math.floor(n.microsecond / 1000))

    def Utc(self):
        """Returns the UTC date and time as a `datetime` object.

        Uses the standard [`datetime`](https://docs.python.org/3/library/datetime.html) class
        to represent the date and time in this Time object.

        Returns
        -------
        `datetime`
        """
        return _EPOCH + datetime.timedelta(days=self.ut)

    def _etilt(self):
        # Calculates precession and nutation of the Earth's axis.
        # The calculations are very expensive, so lazy-evaluate and cache
        # the result inside this Time object.
        if self.etilt is None:
            self.etilt = _e_tilt(self)
        return self.etilt


class Observer:
    """Represents the geographic location of an observer on the surface of the Earth.

    Parameters
    ----------
    latitude : float
        Geographic latitude in degrees north of the equator.
    longitude : float
        Geographic longitude in degrees east of the prime meridian at Greenwich, England.
    height : float
        Elevation above sea level in meters.
    """
    def __init__(self, latitude, longitude, height=0):
        self.latitude = latitude
        self.longitude = longitude
        self.height = height

class RotationMatrix:
    """Contains a rotation matrix that can be used to transform one
    coordinate system into another.

    Parameters
    ----------
    rot : float[3][3]
        A normalized 3x3 rotation matrix.
    """
    def __init__(self, rot):
        self.rot = rot

class Spherical:
    """Holds spherical coordinates: latitude, longitude, distance.

    Parameters
    ----------
    lat : float
        The latitude angle: -90..+90 degrees.
    lon : float
        The longitude angle: 0..360 degrees.
    dist : float
        Distance in AU.
    """
    def __init__(self, lat, lon, dist):
        self.lat = lat
        self.lon = lon
        self.dist = dist

class _iau2000b:
    def __init__(self, time):
        t = time.tt / 36525.0
        el  = math.fmod((485868.249036 + t*1717915923.2178), _ASEC360) * _ASEC2RAD
        elp = math.fmod((1287104.79305 + t*129596581.0481),  _ASEC360) * _ASEC2RAD
        f   = math.fmod((335779.526232 + t*1739527262.8478), _ASEC360) * _ASEC2RAD
        d   = math.fmod((1072260.70369 + t*1602961601.2090), _ASEC360) * _ASEC2RAD
        om  = math.fmod((450160.398036 - t*6962890.5431),    _ASEC360) * _ASEC2RAD
        dp = 0
        de = 0


        sarg = math.sin(om)
        carg = math.cos(om)
        dp += (-172064161.0 - 174666.0*t)*sarg + 33386.0*carg
        de += (92052331.0 + 9086.0*t)*carg + 15377.0*sarg


        arg = 2.0*f - 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-13170906.0 - 1675.0*t)*sarg - 13696.0*carg
        de += (5730336.0 - 3015.0*t)*carg - 4587.0*sarg


        arg = 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-2276413.0 - 234.0*t)*sarg + 2796.0*carg
        de += (978459.0 - 485.0*t)*carg + 1374.0*sarg


        arg = 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (2074554.0 + 207.0*t)*sarg - 698.0*carg
        de += (-897492.0 + 470.0*t)*carg - 291.0*sarg


        sarg = math.sin(elp)
        carg = math.cos(elp)
        dp += (1475877.0 - 3633.0*t)*sarg + 11817.0*carg
        de += (73871.0 - 184.0*t)*carg - 1924.0*sarg


        arg = elp + 2.0*f - 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-516821.0 + 1226.0*t)*sarg - 524.0*carg
        de += (224386.0 - 677.0*t)*carg - 174.0*sarg


        sarg = math.sin(el)
        carg = math.cos(el)
        dp += (711159.0 + 73.0*t)*sarg - 872.0*carg
        de += (-6750.0)*carg + 358.0*sarg


        arg = 2.0*f + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-387298.0 - 367.0*t)*sarg + 380.0*carg
        de += (200728.0 + 18.0*t)*carg + 318.0*sarg


        arg = el + 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-301461.0 - 36.0*t)*sarg + 816.0*carg
        de += (129025.0 - 63.0*t)*carg + 367.0*sarg


        arg = -elp + 2.0*f - 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (215829.0 - 494.0*t)*sarg + 111.0*carg
        de += (-95929.0 + 299.0*t)*carg + 132.0*sarg


        arg = 2.0*f - 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (128227.0 + 137.0*t)*sarg + 181.0*carg
        de += (-68982.0 - 9.0*t)*carg + 39.0*sarg


        arg = -el + 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (123457.0 + 11.0*t)*sarg + 19.0*carg
        de += (-53311.0 + 32.0*t)*carg - 4.0*sarg


        arg = -el + 2.0*d
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (156994.0 + 10.0*t)*sarg - 168.0*carg
        de += (-1235.0)*carg + 82.0*sarg


        arg = el + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (63110.0 + 63.0*t)*sarg + 27.0*carg
        de += (-33228.0)*carg - 9.0*sarg


        arg = -el + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-57976.0 - 63.0*t)*sarg - 189.0*carg
        de += (31429.0)*carg - 75.0*sarg


        arg = -el + 2.0*f + 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-59641.0 - 11.0*t)*sarg + 149.0*carg
        de += (25543.0 - 11.0*t)*carg + 66.0*sarg


        arg = el + 2.0*f + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-51613.0 - 42.0*t)*sarg + 129.0*carg
        de += (26366.0)*carg + 78.0*sarg


        arg = -2.0*el + 2.0*f + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (45893.0 + 50.0*t)*sarg + 31.0*carg
        de += (-24236.0 - 10.0*t)*carg + 20.0*sarg


        arg = 2.0*d
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (63384.0 + 11.0*t)*sarg - 150.0*carg
        de += (-1220.0)*carg + 29.0*sarg


        arg = 2.0*f + 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-38571.0 - 1.0*t)*sarg + 158.0*carg
        de += (16452.0 - 11.0*t)*carg + 68.0*sarg


        arg = -2.0*elp + 2.0*f - 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (32481.0)*sarg
        de += (-13870.0)*carg


        arg = -2.0*el + 2.0*d
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-47722.0)*sarg - 18.0*carg
        de += (477.0)*carg - 25.0*sarg


        arg = 2.0*el + 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-31046.0 - 1.0*t)*sarg + 131.0*carg
        de += (13238.0 - 11.0*t)*carg + 59.0*sarg


        arg = el + 2.0*f - 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (28593.0)*sarg - carg
        de += (-12338.0 + 10.0*t)*carg - 3.0*sarg


        arg = -el + 2.0*f + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (20441.0 + 21.0*t)*sarg + 10.0*carg
        de += (-10758.0)*carg - 3.0*sarg


        arg = 2.0*el
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (29243.0)*sarg - 74.0*carg
        de += (-609.0)*carg + 13.0*sarg


        arg = 2.0*f
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (25887.0)*sarg - 66.0*carg
        de += (-550.0)*carg + 11.0*sarg


        arg = elp + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-14053.0 - 25.0*t)*sarg + 79.0*carg
        de += (8551.0 - 2.0*t)*carg - 45.0*sarg


        arg = -el + 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (15164.0 + 10.0*t)*sarg + 11.0*carg
        de += (-8001.0)*carg - sarg


        arg = 2.0*elp + 2.0*f - 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-15794.0 + 72.0*t)*sarg - 16.0*carg
        de += (6850.0 - 42.0*t)*carg - 5.0*sarg


        arg = -2.0*f + 2.0*d
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (21783.0)*sarg + 13.0*carg
        de += (-167.0)*carg + 13.0*sarg


        arg = el - 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-12873.0 - 10.0*t)*sarg - 37.0*carg
        de += (6953.0)*carg - 14.0*sarg


        arg = -elp + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-12654.0 + 11.0*t)*sarg + 63.0*carg
        de += (6415.0)*carg + 26.0*sarg


        arg = -el + 2.0*f + 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-10204.0)*sarg + 25.0*carg
        de += (5222.0)*carg + 15.0*sarg


        arg = 2.0*elp
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (16707.0 - 85.0*t)*sarg - 10.0*carg
        de += (168.0 - 1.0*t)*carg + 10.0*sarg


        arg = el + 2.0*f + 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-7691.0)*sarg + 44.0*carg
        de += (3268.0)*carg + 19.0*sarg


        arg = -2.0*el + 2.0*f
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-11024.0)*sarg - 14.0*carg
        de += (104.0)*carg + 2.0*sarg


        arg = elp + 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (7566.0 - 21.0*t)*sarg - 11.0*carg
        de += (-3250.0)*carg - 5.0*sarg


        arg = 2.0*f + 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-6637.0 - 11.0*t)*sarg + 25.0*carg
        de += (3353.0)*carg + 14.0*sarg


        arg = -elp + 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-7141.0 + 21.0*t)*sarg + 8.0*carg
        de += (3070.0)*carg + 4.0*sarg


        arg = 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-6302.0 - 11.0*t)*sarg + 2.0*carg
        de += (3272.0)*carg + 4.0*sarg


        arg = el + 2.0*f - 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (5800.0 + 10.0*t)*sarg + 2.0*carg
        de += (-3045.0)*carg - sarg


        arg = 2.0*el + 2.0*f - 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (6443.0)*sarg - 7.0*carg
        de += (-2768.0)*carg - 4.0*sarg


        arg = -2.0*el + 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-5774.0 - 11.0*t)*sarg - 15.0*carg
        de += (3041.0)*carg - 5.0*sarg


        arg = 2.0*el + 2.0*f + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-5350.0)*sarg + 21.0*carg
        de += (2695.0)*carg + 12.0*sarg


        arg = -elp + 2.0*f - 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-4752.0 - 11.0*t)*sarg - 3.0*carg
        de += (2719.0)*carg - 3.0*sarg


        arg = -2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-4940.0 - 11.0*t)*sarg - 21.0*carg
        de += (2720.0)*carg - 9.0*sarg


        arg = -el - elp + 2.0*d
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (7350.0)*sarg - 8.0*carg
        de += (-51.0)*carg + 4.0*sarg


        arg = 2.0*el - 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (4065.0)*sarg + 6.0*carg
        de += (-2206.0)*carg + sarg


        arg = el + 2.0*d
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (6579.0)*sarg - 24.0*carg
        de += (-199.0)*carg + 2.0*sarg


        arg = elp + 2.0*f - 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (3579.0)*sarg + 5.0*carg
        de += (-1900.0)*carg + sarg


        arg = el - elp
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (4725.0)*sarg - 6.0*carg
        de += (-41.0)*carg + 3.0*sarg


        arg = -2.0*el + 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-3075.0)*sarg - 2.0*carg
        de += (1313.0)*carg - sarg


        arg = 3.0*el + 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-2904.0)*sarg + 15.0*carg
        de += (1233.0)*carg + 7.0*sarg


        arg = -elp + 2.0*d
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (4348.0)*sarg - 10.0*carg
        de += (-81.0)*carg + 2.0*sarg


        arg = el - elp + 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-2878.0)*sarg + 8.0*carg
        de += (1232.0)*carg + 4.0*sarg


        sarg = math.sin(d)
        carg = math.cos(d)
        dp += (-4230.0)*sarg + 5.0*carg
        de += (-20.0)*carg - 2.0*sarg


        arg = -el - elp + 2.0*f + 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-2819.0)*sarg + 7.0*carg
        de += (1207.0)*carg + 3.0*sarg


        arg = -el + 2.0*f
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-4056.0)*sarg + 5.0*carg
        de += (40.0)*carg - 2.0*sarg


        arg = -elp + 2.0*f + 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-2647.0)*sarg + 11.0*carg
        de += (1129.0)*carg + 5.0*sarg


        arg = -2.0*el + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-2294.0)*sarg - 10.0*carg
        de += (1266.0)*carg - 4.0*sarg


        arg = el + elp + 2.0*f + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (2481.0)*sarg - 7.0*carg
        de += (-1062.0)*carg - 3.0*sarg


        arg = 2.0*el + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (2179.0)*sarg - 2.0*carg
        de += (-1129.0)*carg - 2.0*sarg


        arg = -el + elp + d
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (3276.0)*sarg + carg
        de += (-9.0)*carg


        arg = el + elp
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-3389.0)*sarg + 5.0*carg
        de += (35.0)*carg - 2.0*sarg


        arg = el + 2.0*f
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (3339.0)*sarg - 13.0*carg
        de += (-107.0)*carg + sarg


        arg = -el + 2.0*f - 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-1987.0)*sarg - 6.0*carg
        de += (1073.0)*carg - 2.0*sarg


        arg = el + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-1981.0)*sarg
        de += (854.0)*carg


        arg = -el + d
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (4026.0)*sarg - 353.0*carg
        de += (-553.0)*carg - 139.0*sarg


        arg = 2.0*f + d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (1660.0)*sarg - 5.0*carg
        de += (-710.0)*carg - 2.0*sarg


        arg = -el + 2.0*f + 4.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-1521.0)*sarg + 9.0*carg
        de += (647.0)*carg + 4.0*sarg


        arg = -el + elp + d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (1314.0)*sarg
        de += (-700.0)*carg


        arg = -2.0*elp + 2.0*f - 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-1283.0)*sarg
        de += (672.0)*carg


        arg = el + 2.0*f + 2.0*d + om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (-1331.0)*sarg + 8.0*carg
        de += (663.0)*carg + 4.0*sarg


        arg = -2.0*el + 2.0*f + 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (1383.0)*sarg - 2.0*carg
        de += (-594.0)*carg - 2.0*sarg


        arg = -el + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (1405.0)*sarg + 4.0*carg
        de += (-610.0)*carg + 2.0*sarg


        arg = el + elp + 2.0*f - 2.0*d + 2.0*om
        sarg = math.sin(arg)
        carg = math.cos(arg)
        dp += (1290.0)*sarg
        de += (-556.0)*carg


        self.dpsi = -0.000135 + (dp * 1.0e-7)
        self.deps = +0.000388 + (de * 1.0e-7)

def _mean_obliq(tt):
    t = tt / 36525
    asec = (
        (((( -  0.0000000434   * t
             -  0.000000576  ) * t
             +  0.00200340   ) * t
             -  0.0001831    ) * t
             - 46.836769     ) * t + 84381.406
    )
    return asec / 3600.0

class _e_tilt:
    def __init__(self, time):
        e = _iau2000b(time)
        self.dpsi = e.dpsi
        self.deps = e.deps
        self.mobl = _mean_obliq(time.tt)
        self.tobl = self.mobl + (e.deps / 3600.0)
        self.tt = time.tt
        self.ee = e.dpsi * math.cos(math.radians(self.mobl)) / 15.0

def _ecl2equ_vec(time, ecl):
    obl = math.radians(_mean_obliq(time.tt))
    cos_obl = math.cos(obl)
    sin_obl = math.sin(obl)
    return [
        ecl[0],
        ecl[1]*cos_obl - ecl[2]*sin_obl,
        ecl[1]*sin_obl + ecl[2]*cos_obl
    ]

def _precession_rot(tt1, tt2):
    eps0 = 84381.406
    if tt1 != 0 and tt2 != 0:
        raise Error('One of (tt1, tt2) must be zero.')
    t = (tt2 - tt1) / 36525
    if tt2 == 0:
        t = -t

    psia  = (((((-    0.0000000951  * t
                 +    0.000132851 ) * t
                 -    0.00114045  ) * t
                 -    1.0790069   ) * t
                 + 5038.481507    ) * t)

    omegaa = (((((+   0.0000003337  * t
                 -    0.000000467 ) * t
                 -    0.00772503  ) * t
                 +    0.0512623   ) * t
                 -    0.025754    ) * t + eps0)

    chia  = (((((-    0.0000000560  * t
                 +    0.000170663 ) * t
                 -    0.00121197  ) * t
                 -    2.3814292   ) * t
                 +   10.556403    ) * t)

    eps0 *= _ASEC2RAD
    psia *= _ASEC2RAD
    omegaa *= _ASEC2RAD
    chia *= _ASEC2RAD

    sa = math.sin(eps0)
    ca = math.cos(eps0)
    sb = math.sin(-psia)
    cb = math.cos(-psia)
    sc = math.sin(-omegaa)
    cc = math.cos(-omegaa)
    sd = math.sin(chia)
    cd = math.cos(chia)

    xx =  cd * cb - sb * sd * cc
    yx =  cd * sb * ca + sd * cc * cb * ca - sa * sd * sc
    zx =  cd * sb * sa + sd * cc * cb * sa + ca * sd * sc
    xy = -sd * cb - sb * cd * cc
    yy = -sd * sb * ca + cd * cc * cb * ca - sa * cd * sc
    zy = -sd * sb * sa + cd * cc * cb * sa + ca * cd * sc
    xz =  sb * sc
    yz = -sc * cb * ca - sa * cc
    zz = -sc * cb * sa + cc * ca
    if tt2 == 0.0:
        # Perform rotation from other epoch to J2000.0.
        return RotationMatrix([
            [xx, yx, zx],
            [xy, yy, zy],
            [xz, yz, zz]
        ])

    # Perform rotation from J2000.0 to other epoch.
    return RotationMatrix([
        [xx, xy, xz],
        [yx, yy, yz],
        [zx, zy, zz]
    ])

def _precession(tt1, pos1, tt2):
    r = _precession_rot(tt1, tt2)
    return [
        r.rot[0][0]*pos1[0] + r.rot[1][0]*pos1[1] + r.rot[2][0]*pos1[2],
        r.rot[0][1]*pos1[0] + r.rot[1][1]*pos1[1] + r.rot[2][1]*pos1[2],
        r.rot[0][2]*pos1[0] + r.rot[1][2]*pos1[1] + r.rot[2][2]*pos1[2]
    ]

class Equatorial:
    """Equatorial angular coordinates

    Coordinates of a celestial body as seen from the Earth.
    Can be geocentric or topocentric, depending on context.
    The coordinates are oriented with respect to the Earth's
    equator projected onto the sky.

    Attributes
    ----------
    ra : float
        Right ascension in sidereal hours.
    dec : float
        Declination in degrees.
    dist : float
        Distance to the celestial body in AU.
    """
    def __init__(self, ra, dec, dist):
        self.ra = ra
        self.dec = dec
        self.dist = dist

def _vector2radec(pos):
    xyproj = pos[0]*pos[0] + pos[1]*pos[1]
    dist = math.sqrt(xyproj + pos[2]*pos[2])
    if xyproj == 0.0:
        if pos[2] == 0.0:
            # Indeterminate coordinates: pos vector has zero length.
            raise BadVectorError()
        ra = 0.0
        if pos[2] < 0.0:
            dec = -90.0
        else:
            dec = +90.0
    else:
        ra = math.degrees(math.atan2(pos[1], pos[0])) / 15.0
        if ra < 0:
            ra += 24
        dec = math.degrees(math.atan2(pos[2], math.sqrt(xyproj)))
    return Equatorial(ra, dec, dist)


def _nutation_rot(time, direction):
    tilt = time._etilt()
    oblm = math.radians(tilt.mobl)
    oblt = math.radians(tilt.tobl)
    psi = tilt.dpsi * _ASEC2RAD
    cobm = math.cos(oblm)
    sobm = math.sin(oblm)
    cobt = math.cos(oblt)
    sobt = math.sin(oblt)
    cpsi = math.cos(psi)
    spsi = math.sin(psi)

    xx = cpsi
    yx = -spsi * cobm
    zx = -spsi * sobm
    xy = spsi * cobt
    yy = cpsi * cobm * cobt + sobm * sobt
    zy = cpsi * sobm * cobt - cobm * sobt
    xz = spsi * sobt
    yz = cpsi * cobm * sobt - sobm * cobt
    zz = cpsi * sobm * sobt + cobm * cobt

    if direction == 0:
        # forward rotation
        return RotationMatrix([
            [xx, xy, xz],
            [yx, yy, yz],
            [zx, zy, zz]
        ])

    # inverse rotation
    return RotationMatrix([
        [xx, yx, zx],
        [xy, yy, zy],
        [xz, yz, zz]
    ])

def _nutation(time, direction, pos):
    r = _nutation_rot(time, direction)
    return [
        r.rot[0][0]*pos[0] + r.rot[1][0]*pos[1] + r.rot[2][0]*pos[2],
        r.rot[0][1]*pos[0] + r.rot[1][1]*pos[1] + r.rot[2][1]*pos[2],
        r.rot[0][2]*pos[0] + r.rot[1][2]*pos[1] + r.rot[2][2]*pos[2]
    ]

def _era(time):        # Earth Rotation Angle
    thet1 = 0.7790572732640 + 0.00273781191135448 * time.ut
    thet3 = math.fmod(time.ut, 1.0)
    theta = 360.0 * math.fmod((thet1 + thet3), 1.0)
    if theta < 0.0:
        theta += 360.0
    return theta


def _sidereal_time(time):
    t = time.tt / 36525.0
    eqeq = 15.0 * time._etilt().ee    # Replace with eqeq=0 to get GMST instead of GAST (if we ever need it)
    theta = _era(time)
    st = (eqeq + 0.014506 +
        (((( -    0.0000000368   * t
            -    0.000029956  ) * t
            -    0.00000044   ) * t
            +    1.3915817    ) * t
            + 4612.156534     ) * t)
    gst = math.fmod((st/3600.0 + theta), 360.0) / 15.0
    if gst < 0.0:
        gst += 24.0
    return gst


def _terra(observer, st):
    erad_km = _ERAD / 1000.0
    df = 1.0 - 0.003352819697896    # flattening of the Earth
    df2 = df * df
    phi = math.radians(observer.latitude)
    sinphi = math.sin(phi)
    cosphi = math.cos(phi)
    c = 1.0 / math.sqrt(cosphi*cosphi + df2*sinphi*sinphi)
    s = df2 * c
    ht_km = observer.height / 1000.0
    ach = erad_km*c + ht_km
    ash = erad_km*s + ht_km
    stlocl = math.radians(15.0*st + observer.longitude)
    sinst = math.sin(stlocl)
    cosst = math.cos(stlocl)
    return [
        ach * cosphi * cosst / _KM_PER_AU,
        ach * cosphi * sinst / _KM_PER_AU,
        ash * sinphi / _KM_PER_AU
    ]

def _geo_pos(time, observer):
    gast = _sidereal_time(time)
    pos1 = _terra(observer, gast)
    pos2 = _nutation(time, -1, pos1)
    outpos = _precession(time.tt, pos2, 0.0)
    return outpos

def _spin(angle, pos1):
    angr = math.radians(angle)
    cosang = math.cos(angr)
    sinang = math.sin(angr)
    return [
        +cosang*pos1[0] + sinang*pos1[1],
        -sinang*pos1[0] + cosang*pos1[1],
        pos1[2]
    ]

#----------------------------------------------------------------------------
# BEGIN CalcMoon

def _Array1(xmin, xmax):
    return dict((key, 0j) for key in range(xmin, 1+xmax))

def _Array2(xmin, xmax, ymin, ymax):
    return dict((key, _Array1(ymin, ymax)) for key in range(xmin, 1+xmax))

class _moonpos:
    def __init__(self, lon, lat, dist):
        self.geo_eclip_lon = lon
        self.geo_eclip_lat = lat
        self.distance_au = dist

def _CalcMoon(time):
    T = time.tt / 36525
    ex = _Array2(-6, 6, 1, 4)

    def Sine(phi):
        return math.sin(_PI2 * phi)

    def Frac(x):
        return x - math.floor(x)

    T2 = T*T
    DLAM = 0
    DS = 0
    GAM1C = 0
    SINPI = 3422.7000
    S1 = Sine(0.19833+0.05611*T)
    S2 = Sine(0.27869+0.04508*T)
    S3 = Sine(0.16827-0.36903*T)
    S4 = Sine(0.34734-5.37261*T)
    S5 = Sine(0.10498-5.37899*T)
    S6 = Sine(0.42681-0.41855*T)
    S7 = Sine(0.14943-5.37511*T)
    DL0 = 0.84*S1+0.31*S2+14.27*S3+ 7.26*S4+ 0.28*S5+0.24*S6
    DL  = 2.94*S1+0.31*S2+14.27*S3+ 9.34*S4+ 1.12*S5+0.83*S6
    DLS =-6.40*S1                                   -1.89*S6
    DF  = 0.21*S1+0.31*S2+14.27*S3-88.70*S4-15.30*S5+0.24*S6-1.86*S7
    DD  = DL0-DLS
    DGAM  = ((-3332E-9 * Sine(0.59734-5.37261*T)
               -539E-9 * Sine(0.35498-5.37899*T)
                -64E-9 * Sine(0.39943-5.37511*T)))

    L0 = _PI2*Frac(0.60643382+1336.85522467*T-0.00000313*T2) + DL0/_ARC
    L  = _PI2*Frac(0.37489701+1325.55240982*T+0.00002565*T2) + DL /_ARC
    LS = _PI2*Frac(0.99312619+  99.99735956*T-0.00000044*T2) + DLS/_ARC
    F  = _PI2*Frac(0.25909118+1342.22782980*T-0.00000892*T2) + DF /_ARC
    D  = _PI2*Frac(0.82736186+1236.85308708*T-0.00000397*T2) + DD /_ARC

    I = 1
    while I <= 4:
        if I == 1:
            ARG=L; MAX=4; FAC=1.000002208
        elif I == 2:
            ARG=LS; MAX=3; FAC=0.997504612-0.002495388*T
        elif I == 3:
            ARG=F; MAX=4; FAC=1.000002708+139.978*DGAM
        else:
            ARG=D; MAX=6; FAC=1.0

        ex[0][I] = complex(1, 0)
        ex[1][I] = complex(FAC * math.cos(ARG), FAC * math.sin(ARG))

        J = 2
        while J <= MAX:
            ex[J][I] = ex[J-1][I] * ex[1][I]
            J += 1

        J = 1
        while J <= MAX:
            ex[-J][I] = ex[J][I].conjugate()
            J += 1

        I += 1



    # AddSol(13.902000, 14.060000, -0.001000, 0.260700, 0.000000, 0.000000, 0.000000, 4.000000)
    z = ex[4][4]
    DLAM  += 13.902 * z.imag
    DS    += 14.06 * z.imag
    GAM1C += -0.001 * z.real
    SINPI += 0.2607 * z.real

    # AddSol(0.403000, -4.010000, 0.394000, 0.002300, 0.000000, 0.000000, 0.000000, 3.000000)
    z = ex[3][4]
    DLAM  += 0.403 * z.imag
    DS    += -4.01 * z.imag
    GAM1C += 0.394 * z.real
    SINPI += 0.0023 * z.real

    # AddSol(2369.912000, 2373.360000, 0.601000, 28.233300, 0.000000, 0.000000, 0.000000, 2.000000)
    z = ex[2][4]
    DLAM  += 2369.912 * z.imag
    DS    += 2373.36 * z.imag
    GAM1C += 0.601 * z.real
    SINPI += 28.2333 * z.real

    # AddSol(-125.154000, -112.790000, -0.725000, -0.978100, 0.000000, 0.000000, 0.000000, 1.000000)
    z = ex[1][4]
    DLAM  += -125.154 * z.imag
    DS    += -112.79 * z.imag
    GAM1C += -0.725 * z.real
    SINPI += -0.9781 * z.real

    # AddSol(1.979000, 6.980000, -0.445000, 0.043300, 1.000000, 0.000000, 0.000000, 4.000000)
    z = ex[1][1] * ex[4][4]
    DLAM  += 1.979 * z.imag
    DS    += 6.98 * z.imag
    GAM1C += -0.445 * z.real
    SINPI += 0.0433 * z.real

    # AddSol(191.953000, 192.720000, 0.029000, 3.086100, 1.000000, 0.000000, 0.000000, 2.000000)
    z = ex[1][1] * ex[2][4]
    DLAM  += 191.953 * z.imag
    DS    += 192.72 * z.imag
    GAM1C += 0.029 * z.real
    SINPI += 3.0861 * z.real

    # AddSol(-8.466000, -13.510000, 0.455000, -0.109300, 1.000000, 0.000000, 0.000000, 1.000000)
    z = ex[1][1] * ex[1][4]
    DLAM  += -8.466 * z.imag
    DS    += -13.51 * z.imag
    GAM1C += 0.455 * z.real
    SINPI += -0.1093 * z.real

    # AddSol(22639.500000, 22609.070000, 0.079000, 186.539800, 1.000000, 0.000000, 0.000000, 0.000000)
    z = ex[1][1]
    DLAM  += 22639.500 * z.imag
    DS    += 22609.07 * z.imag
    GAM1C += 0.079 * z.real
    SINPI += 186.5398 * z.real

    # AddSol(18.609000, 3.590000, -0.094000, 0.011800, 1.000000, 0.000000, 0.000000, -1.000000)
    z = ex[1][1] * ex[-1][4]
    DLAM  += 18.609 * z.imag
    DS    += 3.59 * z.imag
    GAM1C += -0.094 * z.real
    SINPI += 0.0118 * z.real

    # AddSol(-4586.465000, -4578.130000, -0.077000, 34.311700, 1.000000, 0.000000, 0.000000, -2.000000)
    z = ex[1][1] * ex[-2][4]
    DLAM  += -4586.465 * z.imag
    DS    += -4578.13 * z.imag
    GAM1C += -0.077 * z.real
    SINPI += 34.3117 * z.real

    # AddSol(3.215000, 5.440000, 0.192000, -0.038600, 1.000000, 0.000000, 0.000000, -3.000000)
    z = ex[1][1] * ex[-3][4]
    DLAM  += 3.215 * z.imag
    DS    += 5.44 * z.imag
    GAM1C += 0.192 * z.real
    SINPI += -0.0386 * z.real

    # AddSol(-38.428000, -38.640000, 0.001000, 0.600800, 1.000000, 0.000000, 0.000000, -4.000000)
    z = ex[1][1] * ex[-4][4]
    DLAM  += -38.428 * z.imag
    DS    += -38.64 * z.imag
    GAM1C += 0.001 * z.real
    SINPI += 0.6008 * z.real

    # AddSol(-0.393000, -1.430000, -0.092000, 0.008600, 1.000000, 0.000000, 0.000000, -6.000000)
    z = ex[1][1] * ex[-6][4]
    DLAM  += -0.393 * z.imag
    DS    += -1.43 * z.imag
    GAM1C += -0.092 * z.real
    SINPI += 0.0086 * z.real

    # AddSol(-0.289000, -1.590000, 0.123000, -0.005300, 0.000000, 1.000000, 0.000000, 4.000000)
    z = ex[1][2] * ex[4][4]
    DLAM  += -0.289 * z.imag
    DS    += -1.59 * z.imag
    GAM1C += 0.123 * z.real
    SINPI += -0.0053 * z.real

    # AddSol(-24.420000, -25.100000, 0.040000, -0.300000, 0.000000, 1.000000, 0.000000, 2.000000)
    z = ex[1][2] * ex[2][4]
    DLAM  += -24.420 * z.imag
    DS    += -25.10 * z.imag
    GAM1C += 0.040 * z.real
    SINPI += -0.3000 * z.real

    # AddSol(18.023000, 17.930000, 0.007000, 0.149400, 0.000000, 1.000000, 0.000000, 1.000000)
    z = ex[1][2] * ex[1][4]
    DLAM  += 18.023 * z.imag
    DS    += 17.93 * z.imag
    GAM1C += 0.007 * z.real
    SINPI += 0.1494 * z.real

    # AddSol(-668.146000, -126.980000, -1.302000, -0.399700, 0.000000, 1.000000, 0.000000, 0.000000)
    z = ex[1][2]
    DLAM  += -668.146 * z.imag
    DS    += -126.98 * z.imag
    GAM1C += -1.302 * z.real
    SINPI += -0.3997 * z.real

    # AddSol(0.560000, 0.320000, -0.001000, -0.003700, 0.000000, 1.000000, 0.000000, -1.000000)
    z = ex[1][2] * ex[-1][4]
    DLAM  += 0.560 * z.imag
    DS    += 0.32 * z.imag
    GAM1C += -0.001 * z.real
    SINPI += -0.0037 * z.real

    # AddSol(-165.145000, -165.060000, 0.054000, 1.917800, 0.000000, 1.000000, 0.000000, -2.000000)
    z = ex[1][2] * ex[-2][4]
    DLAM  += -165.145 * z.imag
    DS    += -165.06 * z.imag
    GAM1C += 0.054 * z.real
    SINPI += 1.9178 * z.real

    # AddSol(-1.877000, -6.460000, -0.416000, 0.033900, 0.000000, 1.000000, 0.000000, -4.000000)
    z = ex[1][2] * ex[-4][4]
    DLAM  += -1.877 * z.imag
    DS    += -6.46 * z.imag
    GAM1C += -0.416 * z.real
    SINPI += 0.0339 * z.real

    # AddSol(0.213000, 1.020000, -0.074000, 0.005400, 2.000000, 0.000000, 0.000000, 4.000000)
    z = ex[2][1] * ex[4][4]
    DLAM  += 0.213 * z.imag
    DS    += 1.02 * z.imag
    GAM1C += -0.074 * z.real
    SINPI += 0.0054 * z.real

    # AddSol(14.387000, 14.780000, -0.017000, 0.283300, 2.000000, 0.000000, 0.000000, 2.000000)
    z = ex[2][1] * ex[2][4]
    DLAM  += 14.387 * z.imag
    DS    += 14.78 * z.imag
    GAM1C += -0.017 * z.real
    SINPI += 0.2833 * z.real

    # AddSol(-0.586000, -1.200000, 0.054000, -0.010000, 2.000000, 0.000000, 0.000000, 1.000000)
    z = ex[2][1] * ex[1][4]
    DLAM  += -0.586 * z.imag
    DS    += -1.20 * z.imag
    GAM1C += 0.054 * z.real
    SINPI += -0.0100 * z.real

    # AddSol(769.016000, 767.960000, 0.107000, 10.165700, 2.000000, 0.000000, 0.000000, 0.000000)
    z = ex[2][1]
    DLAM  += 769.016 * z.imag
    DS    += 767.96 * z.imag
    GAM1C += 0.107 * z.real
    SINPI += 10.1657 * z.real

    # AddSol(1.750000, 2.010000, -0.018000, 0.015500, 2.000000, 0.000000, 0.000000, -1.000000)
    z = ex[2][1] * ex[-1][4]
    DLAM  += 1.750 * z.imag
    DS    += 2.01 * z.imag
    GAM1C += -0.018 * z.real
    SINPI += 0.0155 * z.real

    # AddSol(-211.656000, -152.530000, 5.679000, -0.303900, 2.000000, 0.000000, 0.000000, -2.000000)
    z = ex[2][1] * ex[-2][4]
    DLAM  += -211.656 * z.imag
    DS    += -152.53 * z.imag
    GAM1C += 5.679 * z.real
    SINPI += -0.3039 * z.real

    # AddSol(1.225000, 0.910000, -0.030000, -0.008800, 2.000000, 0.000000, 0.000000, -3.000000)
    z = ex[2][1] * ex[-3][4]
    DLAM  += 1.225 * z.imag
    DS    += 0.91 * z.imag
    GAM1C += -0.030 * z.real
    SINPI += -0.0088 * z.real

    # AddSol(-30.773000, -34.070000, -0.308000, 0.372200, 2.000000, 0.000000, 0.000000, -4.000000)
    z = ex[2][1] * ex[-4][4]
    DLAM  += -30.773 * z.imag
    DS    += -34.07 * z.imag
    GAM1C += -0.308 * z.real
    SINPI += 0.3722 * z.real

    # AddSol(-0.570000, -1.400000, -0.074000, 0.010900, 2.000000, 0.000000, 0.000000, -6.000000)
    z = ex[2][1] * ex[-6][4]
    DLAM  += -0.570 * z.imag
    DS    += -1.40 * z.imag
    GAM1C += -0.074 * z.real
    SINPI += 0.0109 * z.real

    # AddSol(-2.921000, -11.750000, 0.787000, -0.048400, 1.000000, 1.000000, 0.000000, 2.000000)
    z = ex[1][1] * ex[1][2] * ex[2][4]
    DLAM  += -2.921 * z.imag
    DS    += -11.75 * z.imag
    GAM1C += 0.787 * z.real
    SINPI += -0.0484 * z.real

    # AddSol(1.267000, 1.520000, -0.022000, 0.016400, 1.000000, 1.000000, 0.000000, 1.000000)
    z = ex[1][1] * ex[1][2] * ex[1][4]
    DLAM  += 1.267 * z.imag
    DS    += 1.52 * z.imag
    GAM1C += -0.022 * z.real
    SINPI += 0.0164 * z.real

    # AddSol(-109.673000, -115.180000, 0.461000, -0.949000, 1.000000, 1.000000, 0.000000, 0.000000)
    z = ex[1][1] * ex[1][2]
    DLAM  += -109.673 * z.imag
    DS    += -115.18 * z.imag
    GAM1C += 0.461 * z.real
    SINPI += -0.9490 * z.real

    # AddSol(-205.962000, -182.360000, 2.056000, 1.443700, 1.000000, 1.000000, 0.000000, -2.000000)
    z = ex[1][1] * ex[1][2] * ex[-2][4]
    DLAM  += -205.962 * z.imag
    DS    += -182.36 * z.imag
    GAM1C += 2.056 * z.real
    SINPI += 1.4437 * z.real

    # AddSol(0.233000, 0.360000, 0.012000, -0.002500, 1.000000, 1.000000, 0.000000, -3.000000)
    z = ex[1][1] * ex[1][2] * ex[-3][4]
    DLAM  += 0.233 * z.imag
    DS    += 0.36 * z.imag
    GAM1C += 0.012 * z.real
    SINPI += -0.0025 * z.real

    # AddSol(-4.391000, -9.660000, -0.471000, 0.067300, 1.000000, 1.000000, 0.000000, -4.000000)
    z = ex[1][1] * ex[1][2] * ex[-4][4]
    DLAM  += -4.391 * z.imag
    DS    += -9.66 * z.imag
    GAM1C += -0.471 * z.real
    SINPI += 0.0673 * z.real

    # AddSol(0.283000, 1.530000, -0.111000, 0.006000, 1.000000, -1.000000, 0.000000, 4.000000)
    z = ex[1][1] * ex[-1][2] * ex[4][4]
    DLAM  += 0.283 * z.imag
    DS    += 1.53 * z.imag
    GAM1C += -0.111 * z.real
    SINPI += 0.0060 * z.real

    # AddSol(14.577000, 31.700000, -1.540000, 0.230200, 1.000000, -1.000000, 0.000000, 2.000000)
    z = ex[1][1] * ex[-1][2] * ex[2][4]
    DLAM  += 14.577 * z.imag
    DS    += 31.70 * z.imag
    GAM1C += -1.540 * z.real
    SINPI += 0.2302 * z.real

    # AddSol(147.687000, 138.760000, 0.679000, 1.152800, 1.000000, -1.000000, 0.000000, 0.000000)
    z = ex[1][1] * ex[-1][2]
    DLAM  += 147.687 * z.imag
    DS    += 138.76 * z.imag
    GAM1C += 0.679 * z.real
    SINPI += 1.1528 * z.real

    # AddSol(-1.089000, 0.550000, 0.021000, 0.000000, 1.000000, -1.000000, 0.000000, -1.000000)
    z = ex[1][1] * ex[-1][2] * ex[-1][4]
    DLAM  += -1.089 * z.imag
    DS    += 0.55 * z.imag
    GAM1C += 0.021 * z.real

    # AddSol(28.475000, 23.590000, -0.443000, -0.225700, 1.000000, -1.000000, 0.000000, -2.000000)
    z = ex[1][1] * ex[-1][2] * ex[-2][4]
    DLAM  += 28.475 * z.imag
    DS    += 23.59 * z.imag
    GAM1C += -0.443 * z.real
    SINPI += -0.2257 * z.real

    # AddSol(-0.276000, -0.380000, -0.006000, -0.003600, 1.000000, -1.000000, 0.000000, -3.000000)
    z = ex[1][1] * ex[-1][2] * ex[-3][4]
    DLAM  += -0.276 * z.imag
    DS    += -0.38 * z.imag
    GAM1C += -0.006 * z.real
    SINPI += -0.0036 * z.real

    # AddSol(0.636000, 2.270000, 0.146000, -0.010200, 1.000000, -1.000000, 0.000000, -4.000000)
    z = ex[1][1] * ex[-1][2] * ex[-4][4]
    DLAM  += 0.636 * z.imag
    DS    += 2.27 * z.imag
    GAM1C += 0.146 * z.real
    SINPI += -0.0102 * z.real

    # AddSol(-0.189000, -1.680000, 0.131000, -0.002800, 0.000000, 2.000000, 0.000000, 2.000000)
    z = ex[2][2] * ex[2][4]
    DLAM  += -0.189 * z.imag
    DS    += -1.68 * z.imag
    GAM1C += 0.131 * z.real
    SINPI += -0.0028 * z.real

    # AddSol(-7.486000, -0.660000, -0.037000, -0.008600, 0.000000, 2.000000, 0.000000, 0.000000)
    z = ex[2][2]
    DLAM  += -7.486 * z.imag
    DS    += -0.66 * z.imag
    GAM1C += -0.037 * z.real
    SINPI += -0.0086 * z.real

    # AddSol(-8.096000, -16.350000, -0.740000, 0.091800, 0.000000, 2.000000, 0.000000, -2.000000)
    z = ex[2][2] * ex[-2][4]
    DLAM  += -8.096 * z.imag
    DS    += -16.35 * z.imag
    GAM1C += -0.740 * z.real
    SINPI += 0.0918 * z.real

    # AddSol(-5.741000, -0.040000, 0.000000, -0.000900, 0.000000, 0.000000, 2.000000, 2.000000)
    z = ex[2][3] * ex[2][4]
    DLAM  += -5.741 * z.imag
    DS    += -0.04 * z.imag
    SINPI += -0.0009 * z.real

    # AddSol(0.255000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 2.000000, 1.000000)
    z = ex[2][3] * ex[1][4]
    DLAM  += 0.255 * z.imag

    # AddSol(-411.608000, -0.200000, 0.000000, -0.012400, 0.000000, 0.000000, 2.000000, 0.000000)
    z = ex[2][3]
    DLAM  += -411.608 * z.imag
    DS    += -0.20 * z.imag
    SINPI += -0.0124 * z.real

    # AddSol(0.584000, 0.840000, 0.000000, 0.007100, 0.000000, 0.000000, 2.000000, -1.000000)
    z = ex[2][3] * ex[-1][4]
    DLAM  += 0.584 * z.imag
    DS    += 0.84 * z.imag
    SINPI += 0.0071 * z.real

    # AddSol(-55.173000, -52.140000, 0.000000, -0.105200, 0.000000, 0.000000, 2.000000, -2.000000)
    z = ex[2][3] * ex[-2][4]
    DLAM  += -55.173 * z.imag
    DS    += -52.14 * z.imag
    SINPI += -0.1052 * z.real

    # AddSol(0.254000, 0.250000, 0.000000, -0.001700, 0.000000, 0.000000, 2.000000, -3.000000)
    z = ex[2][3] * ex[-3][4]
    DLAM  += 0.254 * z.imag
    DS    += 0.25 * z.imag
    SINPI += -0.0017 * z.real

    # AddSol(0.025000, -1.670000, 0.000000, 0.003100, 0.000000, 0.000000, 2.000000, -4.000000)
    z = ex[2][3] * ex[-4][4]
    DLAM  += 0.025 * z.imag
    DS    += -1.67 * z.imag
    SINPI += 0.0031 * z.real

    # AddSol(1.060000, 2.960000, -0.166000, 0.024300, 3.000000, 0.000000, 0.000000, 2.000000)
    z = ex[3][1] * ex[2][4]
    DLAM  += 1.060 * z.imag
    DS    += 2.96 * z.imag
    GAM1C += -0.166 * z.real
    SINPI += 0.0243 * z.real

    # AddSol(36.124000, 50.640000, -1.300000, 0.621500, 3.000000, 0.000000, 0.000000, 0.000000)
    z = ex[3][1]
    DLAM  += 36.124 * z.imag
    DS    += 50.64 * z.imag
    GAM1C += -1.300 * z.real
    SINPI += 0.6215 * z.real

    # AddSol(-13.193000, -16.400000, 0.258000, -0.118700, 3.000000, 0.000000, 0.000000, -2.000000)
    z = ex[3][1] * ex[-2][4]
    DLAM  += -13.193 * z.imag
    DS    += -16.40 * z.imag
    GAM1C += 0.258 * z.real
    SINPI += -0.1187 * z.real

    # AddSol(-1.187000, -0.740000, 0.042000, 0.007400, 3.000000, 0.000000, 0.000000, -4.000000)
    z = ex[3][1] * ex[-4][4]
    DLAM  += -1.187 * z.imag
    DS    += -0.74 * z.imag
    GAM1C += 0.042 * z.real
    SINPI += 0.0074 * z.real

    # AddSol(-0.293000, -0.310000, -0.002000, 0.004600, 3.000000, 0.000000, 0.000000, -6.000000)
    z = ex[3][1] * ex[-6][4]
    DLAM  += -0.293 * z.imag
    DS    += -0.31 * z.imag
    GAM1C += -0.002 * z.real
    SINPI += 0.0046 * z.real

    # AddSol(-0.290000, -1.450000, 0.116000, -0.005100, 2.000000, 1.000000, 0.000000, 2.000000)
    z = ex[2][1] * ex[1][2] * ex[2][4]
    DLAM  += -0.290 * z.imag
    DS    += -1.45 * z.imag
    GAM1C += 0.116 * z.real
    SINPI += -0.0051 * z.real

    # AddSol(-7.649000, -10.560000, 0.259000, -0.103800, 2.000000, 1.000000, 0.000000, 0.000000)
    z = ex[2][1] * ex[1][2]
    DLAM  += -7.649 * z.imag
    DS    += -10.56 * z.imag
    GAM1C += 0.259 * z.real
    SINPI += -0.1038 * z.real

    # AddSol(-8.627000, -7.590000, 0.078000, -0.019200, 2.000000, 1.000000, 0.000000, -2.000000)
    z = ex[2][1] * ex[1][2] * ex[-2][4]
    DLAM  += -8.627 * z.imag
    DS    += -7.59 * z.imag
    GAM1C += 0.078 * z.real
    SINPI += -0.0192 * z.real

    # AddSol(-2.740000, -2.540000, 0.022000, 0.032400, 2.000000, 1.000000, 0.000000, -4.000000)
    z = ex[2][1] * ex[1][2] * ex[-4][4]
    DLAM  += -2.740 * z.imag
    DS    += -2.54 * z.imag
    GAM1C += 0.022 * z.real
    SINPI += 0.0324 * z.real

    # AddSol(1.181000, 3.320000, -0.212000, 0.021300, 2.000000, -1.000000, 0.000000, 2.000000)
    z = ex[2][1] * ex[-1][2] * ex[2][4]
    DLAM  += 1.181 * z.imag
    DS    += 3.32 * z.imag
    GAM1C += -0.212 * z.real
    SINPI += 0.0213 * z.real

    # AddSol(9.703000, 11.670000, -0.151000, 0.126800, 2.000000, -1.000000, 0.000000, 0.000000)
    z = ex[2][1] * ex[-1][2]
    DLAM  += 9.703 * z.imag
    DS    += 11.67 * z.imag
    GAM1C += -0.151 * z.real
    SINPI += 0.1268 * z.real

    # AddSol(-0.352000, -0.370000, 0.001000, -0.002800, 2.000000, -1.000000, 0.000000, -1.000000)
    z = ex[2][1] * ex[-1][2] * ex[-1][4]
    DLAM  += -0.352 * z.imag
    DS    += -0.37 * z.imag
    GAM1C += 0.001 * z.real
    SINPI += -0.0028 * z.real

    # AddSol(-2.494000, -1.170000, -0.003000, -0.001700, 2.000000, -1.000000, 0.000000, -2.000000)
    z = ex[2][1] * ex[-1][2] * ex[-2][4]
    DLAM  += -2.494 * z.imag
    DS    += -1.17 * z.imag
    GAM1C += -0.003 * z.real
    SINPI += -0.0017 * z.real

    # AddSol(0.360000, 0.200000, -0.012000, -0.004300, 2.000000, -1.000000, 0.000000, -4.000000)
    z = ex[2][1] * ex[-1][2] * ex[-4][4]
    DLAM  += 0.360 * z.imag
    DS    += 0.20 * z.imag
    GAM1C += -0.012 * z.real
    SINPI += -0.0043 * z.real

    # AddSol(-1.167000, -1.250000, 0.008000, -0.010600, 1.000000, 2.000000, 0.000000, 0.000000)
    z = ex[1][1] * ex[2][2]
    DLAM  += -1.167 * z.imag
    DS    += -1.25 * z.imag
    GAM1C += 0.008 * z.real
    SINPI += -0.0106 * z.real

    # AddSol(-7.412000, -6.120000, 0.117000, 0.048400, 1.000000, 2.000000, 0.000000, -2.000000)
    z = ex[1][1] * ex[2][2] * ex[-2][4]
    DLAM  += -7.412 * z.imag
    DS    += -6.12 * z.imag
    GAM1C += 0.117 * z.real
    SINPI += 0.0484 * z.real

    # AddSol(-0.311000, -0.650000, -0.032000, 0.004400, 1.000000, 2.000000, 0.000000, -4.000000)
    z = ex[1][1] * ex[2][2] * ex[-4][4]
    DLAM  += -0.311 * z.imag
    DS    += -0.65 * z.imag
    GAM1C += -0.032 * z.real
    SINPI += 0.0044 * z.real

    # AddSol(0.757000, 1.820000, -0.105000, 0.011200, 1.000000, -2.000000, 0.000000, 2.000000)
    z = ex[1][1] * ex[-2][2] * ex[2][4]
    DLAM  += 0.757 * z.imag
    DS    += 1.82 * z.imag
    GAM1C += -0.105 * z.real
    SINPI += 0.0112 * z.real

    # AddSol(2.580000, 2.320000, 0.027000, 0.019600, 1.000000, -2.000000, 0.000000, 0.000000)
    z = ex[1][1] * ex[-2][2]
    DLAM  += 2.580 * z.imag
    DS    += 2.32 * z.imag
    GAM1C += 0.027 * z.real
    SINPI += 0.0196 * z.real

    # AddSol(2.533000, 2.400000, -0.014000, -0.021200, 1.000000, -2.000000, 0.000000, -2.000000)
    z = ex[1][1] * ex[-2][2] * ex[-2][4]
    DLAM  += 2.533 * z.imag
    DS    += 2.40 * z.imag
    GAM1C += -0.014 * z.real
    SINPI += -0.0212 * z.real

    # AddSol(-0.344000, -0.570000, -0.025000, 0.003600, 0.000000, 3.000000, 0.000000, -2.000000)
    z = ex[3][2] * ex[-2][4]
    DLAM  += -0.344 * z.imag
    DS    += -0.57 * z.imag
    GAM1C += -0.025 * z.real
    SINPI += 0.0036 * z.real

    # AddSol(-0.992000, -0.020000, 0.000000, 0.000000, 1.000000, 0.000000, 2.000000, 2.000000)
    z = ex[1][1] * ex[2][3] * ex[2][4]
    DLAM  += -0.992 * z.imag
    DS    += -0.02 * z.imag

    # AddSol(-45.099000, -0.020000, 0.000000, -0.001000, 1.000000, 0.000000, 2.000000, 0.000000)
    z = ex[1][1] * ex[2][3]
    DLAM  += -45.099 * z.imag
    DS    += -0.02 * z.imag
    SINPI += -0.0010 * z.real

    # AddSol(-0.179000, -9.520000, 0.000000, -0.083300, 1.000000, 0.000000, 2.000000, -2.000000)
    z = ex[1][1] * ex[2][3] * ex[-2][4]
    DLAM  += -0.179 * z.imag
    DS    += -9.52 * z.imag
    SINPI += -0.0833 * z.real

    # AddSol(-0.301000, -0.330000, 0.000000, 0.001400, 1.000000, 0.000000, 2.000000, -4.000000)
    z = ex[1][1] * ex[2][3] * ex[-4][4]
    DLAM  += -0.301 * z.imag
    DS    += -0.33 * z.imag
    SINPI += 0.0014 * z.real

    # AddSol(-6.382000, -3.370000, 0.000000, -0.048100, 1.000000, 0.000000, -2.000000, 2.000000)
    z = ex[1][1] * ex[-2][3] * ex[2][4]
    DLAM  += -6.382 * z.imag
    DS    += -3.37 * z.imag
    SINPI += -0.0481 * z.real

    # AddSol(39.528000, 85.130000, 0.000000, -0.713600, 1.000000, 0.000000, -2.000000, 0.000000)
    z = ex[1][1] * ex[-2][3]
    DLAM  += 39.528 * z.imag
    DS    += 85.13 * z.imag
    SINPI += -0.7136 * z.real

    # AddSol(9.366000, 0.710000, 0.000000, -0.011200, 1.000000, 0.000000, -2.000000, -2.000000)
    z = ex[1][1] * ex[-2][3] * ex[-2][4]
    DLAM  += 9.366 * z.imag
    DS    += 0.71 * z.imag
    SINPI += -0.0112 * z.real

    # AddSol(0.202000, 0.020000, 0.000000, 0.000000, 1.000000, 0.000000, -2.000000, -4.000000)
    z = ex[1][1] * ex[-2][3] * ex[-4][4]
    DLAM  += 0.202 * z.imag
    DS    += 0.02 * z.imag

    # AddSol(0.415000, 0.100000, 0.000000, 0.001300, 0.000000, 1.000000, 2.000000, 0.000000)
    z = ex[1][2] * ex[2][3]
    DLAM  += 0.415 * z.imag
    DS    += 0.10 * z.imag
    SINPI += 0.0013 * z.real

    # AddSol(-2.152000, -2.260000, 0.000000, -0.006600, 0.000000, 1.000000, 2.000000, -2.000000)
    z = ex[1][2] * ex[2][3] * ex[-2][4]
    DLAM  += -2.152 * z.imag
    DS    += -2.26 * z.imag
    SINPI += -0.0066 * z.real

    # AddSol(-1.440000, -1.300000, 0.000000, 0.001400, 0.000000, 1.000000, -2.000000, 2.000000)
    z = ex[1][2] * ex[-2][3] * ex[2][4]
    DLAM  += -1.440 * z.imag
    DS    += -1.30 * z.imag
    SINPI += 0.0014 * z.real

    # AddSol(0.384000, -0.040000, 0.000000, 0.000000, 0.000000, 1.000000, -2.000000, -2.000000)
    z = ex[1][2] * ex[-2][3] * ex[-2][4]
    DLAM  += 0.384 * z.imag
    DS    += -0.04 * z.imag

    # AddSol(1.938000, 3.600000, -0.145000, 0.040100, 4.000000, 0.000000, 0.000000, 0.000000)
    z = ex[4][1]
    DLAM  += 1.938 * z.imag
    DS    += 3.60 * z.imag
    GAM1C += -0.145 * z.real
    SINPI += 0.0401 * z.real

    # AddSol(-0.952000, -1.580000, 0.052000, -0.013000, 4.000000, 0.000000, 0.000000, -2.000000)
    z = ex[4][1] * ex[-2][4]
    DLAM  += -0.952 * z.imag
    DS    += -1.58 * z.imag
    GAM1C += 0.052 * z.real
    SINPI += -0.0130 * z.real

    # AddSol(-0.551000, -0.940000, 0.032000, -0.009700, 3.000000, 1.000000, 0.000000, 0.000000)
    z = ex[3][1] * ex[1][2]
    DLAM  += -0.551 * z.imag
    DS    += -0.94 * z.imag
    GAM1C += 0.032 * z.real
    SINPI += -0.0097 * z.real

    # AddSol(-0.482000, -0.570000, 0.005000, -0.004500, 3.000000, 1.000000, 0.000000, -2.000000)
    z = ex[3][1] * ex[1][2] * ex[-2][4]
    DLAM  += -0.482 * z.imag
    DS    += -0.57 * z.imag
    GAM1C += 0.005 * z.real
    SINPI += -0.0045 * z.real

    # AddSol(0.681000, 0.960000, -0.026000, 0.011500, 3.000000, -1.000000, 0.000000, 0.000000)
    z = ex[3][1] * ex[-1][2]
    DLAM  += 0.681 * z.imag
    DS    += 0.96 * z.imag
    GAM1C += -0.026 * z.real
    SINPI += 0.0115 * z.real

    # AddSol(-0.297000, -0.270000, 0.002000, -0.000900, 2.000000, 2.000000, 0.000000, -2.000000)
    z = ex[2][1] * ex[2][2] * ex[-2][4]
    DLAM  += -0.297 * z.imag
    DS    += -0.27 * z.imag
    GAM1C += 0.002 * z.real
    SINPI += -0.0009 * z.real

    # AddSol(0.254000, 0.210000, -0.003000, 0.000000, 2.000000, -2.000000, 0.000000, -2.000000)
    z = ex[2][1] * ex[-2][2] * ex[-2][4]
    DLAM  += 0.254 * z.imag
    DS    += 0.21 * z.imag
    GAM1C += -0.003 * z.real

    # AddSol(-0.250000, -0.220000, 0.004000, 0.001400, 1.000000, 3.000000, 0.000000, -2.000000)
    z = ex[1][1] * ex[3][2] * ex[-2][4]
    DLAM  += -0.250 * z.imag
    DS    += -0.22 * z.imag
    GAM1C += 0.004 * z.real
    SINPI += 0.0014 * z.real

    # AddSol(-3.996000, 0.000000, 0.000000, 0.000400, 2.000000, 0.000000, 2.000000, 0.000000)
    z = ex[2][1] * ex[2][3]
    DLAM  += -3.996 * z.imag
    SINPI += 0.0004 * z.real

    # AddSol(0.557000, -0.750000, 0.000000, -0.009000, 2.000000, 0.000000, 2.000000, -2.000000)
    z = ex[2][1] * ex[2][3] * ex[-2][4]
    DLAM  += 0.557 * z.imag
    DS    += -0.75 * z.imag
    SINPI += -0.0090 * z.real

    # AddSol(-0.459000, -0.380000, 0.000000, -0.005300, 2.000000, 0.000000, -2.000000, 2.000000)
    z = ex[2][1] * ex[-2][3] * ex[2][4]
    DLAM  += -0.459 * z.imag
    DS    += -0.38 * z.imag
    SINPI += -0.0053 * z.real

    # AddSol(-1.298000, 0.740000, 0.000000, 0.000400, 2.000000, 0.000000, -2.000000, 0.000000)
    z = ex[2][1] * ex[-2][3]
    DLAM  += -1.298 * z.imag
    DS    += 0.74 * z.imag
    SINPI += 0.0004 * z.real

    # AddSol(0.538000, 1.140000, 0.000000, -0.014100, 2.000000, 0.000000, -2.000000, -2.000000)
    z = ex[2][1] * ex[-2][3] * ex[-2][4]
    DLAM  += 0.538 * z.imag
    DS    += 1.14 * z.imag
    SINPI += -0.0141 * z.real

    # AddSol(0.263000, 0.020000, 0.000000, 0.000000, 1.000000, 1.000000, 2.000000, 0.000000)
    z = ex[1][1] * ex[1][2] * ex[2][3]
    DLAM  += 0.263 * z.imag
    DS    += 0.02 * z.imag

    # AddSol(0.426000, 0.070000, 0.000000, -0.000600, 1.000000, 1.000000, -2.000000, -2.000000)
    z = ex[1][1] * ex[1][2] * ex[-2][3] * ex[-2][4]
    DLAM  += 0.426 * z.imag
    DS    += 0.07 * z.imag
    SINPI += -0.0006 * z.real

    # AddSol(-0.304000, 0.030000, 0.000000, 0.000300, 1.000000, -1.000000, 2.000000, 0.000000)
    z = ex[1][1] * ex[-1][2] * ex[2][3]
    DLAM  += -0.304 * z.imag
    DS    += 0.03 * z.imag
    SINPI += 0.0003 * z.real

    # AddSol(-0.372000, -0.190000, 0.000000, -0.002700, 1.000000, -1.000000, -2.000000, 2.000000)
    z = ex[1][1] * ex[-1][2] * ex[-2][3] * ex[2][4]
    DLAM  += -0.372 * z.imag
    DS    += -0.19 * z.imag
    SINPI += -0.0027 * z.real

    # AddSol(0.418000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 4.000000, 0.000000)
    z = ex[4][3]
    DLAM  += 0.418 * z.imag

    # AddSol(-0.330000, -0.040000, 0.000000, 0.000000, 3.000000, 0.000000, 2.000000, 0.000000)
    z = ex[3][1] * ex[2][3]
    DLAM  += -0.330 * z.imag
    DS    += -0.04 * z.imag


    def ADDN(coeffn, p, q, r, s):
        return coeffn * (ex[p][1] * ex[q][2] * ex[r][3] * ex[s][4]).imag

    N = 0
    N += ADDN(-526.069, 0, 0,1,-2)
    N += ADDN(  -3.352, 0, 0,1,-4)
    N += ADDN( +44.297,+1, 0,1,-2)
    N += ADDN(  -6.000,+1, 0,1,-4)
    N += ADDN( +20.599,-1, 0,1, 0)
    N += ADDN( -30.598,-1, 0,1,-2)
    N += ADDN( -24.649,-2, 0,1, 0)
    N += ADDN(  -2.000,-2, 0,1,-2)
    N += ADDN( -22.571, 0,+1,1,-2)
    N += ADDN( +10.985, 0,-1,1,-2)

    DLAM += (
        +0.82*Sine(0.7736  -62.5512*T)+0.31*Sine(0.0466 -125.1025*T)
        +0.35*Sine(0.5785  -25.1042*T)+0.66*Sine(0.4591+1335.8075*T)
        +0.64*Sine(0.3130  -91.5680*T)+1.14*Sine(0.1480+1331.2898*T)
        +0.21*Sine(0.5918+1056.5859*T)+0.44*Sine(0.5784+1322.8595*T)
        +0.24*Sine(0.2275   -5.7374*T)+0.28*Sine(0.2965   +2.6929*T)
        +0.33*Sine(0.3132   +6.3368*T)
    )
    S = F + DS/_ARC
    lat_seconds = (1.000002708 + 139.978*DGAM)*(18518.511+1.189+GAM1C)*math.sin(S) - 6.24*math.sin(3*S) + N
    return _moonpos(
        _PI2 * Frac((L0+DLAM/_ARC) / _PI2),
        (math.pi / (180 * 3600)) * lat_seconds,
        (_ARC * (_ERAD / _AU)) / (0.999953253 * SINPI)
    )

def GeoMoon(time):
    """Calculates the geocentric position of the Moon at a given time.

    Given a time of observation, calculates the Moon's position as a vector.
    The vector gives the location of the Moon's center relative to the Earth's center
    with x-, y-, and z-components measured in astronomical units.

    This algorithm is based on Nautical Almanac Office's *Improved Lunar Ephemeris* of 1954,
    which in turn derives from E. W. Brown's lunar theories from the early twentieth century.
    It is adapted from Turbo Pascal code from the book
    [Astronomy on the Personal Computer](https://www.springer.com/us/book/9783540672210)
    by Montenbruck and Pfleger.

    Parameters
    ----------
    time : Time
        The date and time for which to calculate the Moon's position.

    Returns
    -------
    #Vector
        The Moon's position as a vector in J2000 Cartesian equatorial coordinates.

    """
    m = _CalcMoon(time)

    # Convert geocentric ecliptic spherical coordinates to Cartesian coordinates.
    dist_cos_lat = m.distance_au * math.cos(m.geo_eclip_lat)
    gepos = [
        dist_cos_lat * math.cos(m.geo_eclip_lon),
        dist_cos_lat * math.sin(m.geo_eclip_lon),
        m.distance_au * math.sin(m.geo_eclip_lat)
    ]

    # Convert ecliptic coordinates to equatorial coordinates, both in mean equinox of date.
    mpos1 = _ecl2equ_vec(time, gepos)

    # Convert from mean equinox of date to J2000.
    mpos2 = _precession(time.tt, mpos1, 0)
    return Vector(mpos2[0], mpos2[1], mpos2[2], time)

# END CalcMoon
#----------------------------------------------------------------------------
# BEGIN VSOP

_vsop = [
    # Mercury
    [
  [
    [
      [4.40250710144, 0.00000000000, 0.00000000000],
      [0.40989414977, 1.48302034195, 26087.90314157420],
      [0.05046294200, 4.47785489551, 52175.80628314840],
      [0.00855346844, 1.16520322459, 78263.70942472259],
      [0.00165590362, 4.11969163423, 104351.61256629678],
      [0.00034561897, 0.77930768443, 130439.51570787099],
      [0.00007583476, 3.71348404924, 156527.41884944518]
    ],
    [
      [26087.90313685529, 0.00000000000, 0.00000000000],
      [0.01131199811, 6.21874197797, 26087.90314157420],
      [0.00292242298, 3.04449355541, 52175.80628314840],
      [0.00075775081, 6.08568821653, 78263.70942472259],
      [0.00019676525, 2.80965111777, 104351.61256629678]
    ]
  ],
  [
    [
      [0.11737528961, 1.98357498767, 26087.90314157420],
      [0.02388076996, 5.03738959686, 52175.80628314840],
      [0.01222839532, 3.14159265359, 0.00000000000],
      [0.00543251810, 1.79644363964, 78263.70942472259],
      [0.00129778770, 4.83232503958, 104351.61256629678],
      [0.00031866927, 1.58088495658, 130439.51570787099],
      [0.00007963301, 4.60972126127, 156527.41884944518]
    ],
    [
      [0.00274646065, 3.95008450011, 26087.90314157420],
      [0.00099737713, 3.14159265359, 0.00000000000]
    ]
  ],
  [
    [
      [0.39528271651, 0.00000000000, 0.00000000000],
      [0.07834131818, 6.19233722598, 26087.90314157420],
      [0.00795525558, 2.95989690104, 52175.80628314840],
      [0.00121281764, 6.01064153797, 78263.70942472259],
      [0.00021921969, 2.77820093972, 104351.61256629678],
      [0.00004354065, 5.82894543774, 130439.51570787099]
    ],
    [
      [0.00217347740, 4.65617158665, 26087.90314157420],
      [0.00044141826, 1.42385544001, 52175.80628314840]
    ]
  ]
],

    # Venus
    [
  [
    [
      [3.17614666774, 0.00000000000, 0.00000000000],
      [0.01353968419, 5.59313319619, 10213.28554621100],
      [0.00089891645, 5.30650047764, 20426.57109242200],
      [0.00005477194, 4.41630661466, 7860.41939243920],
      [0.00003455741, 2.69964447820, 11790.62908865880],
      [0.00002372061, 2.99377542079, 3930.20969621960],
      [0.00001317168, 5.18668228402, 26.29831979980],
      [0.00001664146, 4.25018630147, 1577.34354244780],
      [0.00001438387, 4.15745084182, 9683.59458111640],
      [0.00001200521, 6.15357116043, 30639.85663863300]
    ],
    [
      [10213.28554621638, 0.00000000000, 0.00000000000],
      [0.00095617813, 2.46406511110, 10213.28554621100],
      [0.00007787201, 0.62478482220, 20426.57109242200]
    ]
  ],
  [
    [
      [0.05923638472, 0.26702775812, 10213.28554621100],
      [0.00040107978, 1.14737178112, 20426.57109242200],
      [0.00032814918, 3.14159265359, 0.00000000000]
    ],
    [
      [0.00287821243, 1.88964962838, 10213.28554621100]
    ]
  ],
  [
    [
      [0.72334820891, 0.00000000000, 0.00000000000],
      [0.00489824182, 4.02151831717, 10213.28554621100],
      [0.00001658058, 4.90206728031, 20426.57109242200]
    ],
    [
      [0.00034551041, 0.89198706276, 10213.28554621100]
    ]
  ]
],

    # Earth
    [
  [
    [
      [1.75347045673, 0.00000000000, 0.00000000000],
      [0.03341656453, 4.66925680415, 6283.07584999140],
      [0.00034894275, 4.62610242189, 12566.15169998280],
      [0.00003417572, 2.82886579754, 3.52311834900],
      [0.00003497056, 2.74411783405, 5753.38488489680],
      [0.00003135899, 3.62767041756, 77713.77146812050],
      [0.00002676218, 4.41808345438, 7860.41939243920],
      [0.00002342691, 6.13516214446, 3930.20969621960],
      [0.00001273165, 2.03709657878, 529.69096509460],
      [0.00001324294, 0.74246341673, 11506.76976979360],
      [0.00000901854, 2.04505446477, 26.29831979980],
      [0.00001199167, 1.10962946234, 1577.34354244780],
      [0.00000857223, 3.50849152283, 398.14900340820],
      [0.00000779786, 1.17882681962, 5223.69391980220],
      [0.00000990250, 5.23268072088, 5884.92684658320],
      [0.00000753141, 2.53339052847, 5507.55323866740],
      [0.00000505267, 4.58292599973, 18849.22754997420],
      [0.00000492392, 4.20505711826, 775.52261132400],
      [0.00000356672, 2.91954114478, 0.06731030280],
      [0.00000284125, 1.89869240932, 796.29800681640],
      [0.00000242879, 0.34481445893, 5486.77784317500],
      [0.00000317087, 5.84901948512, 11790.62908865880],
      [0.00000271112, 0.31486255375, 10977.07880469900],
      [0.00000206217, 4.80646631478, 2544.31441988340],
      [0.00000205478, 1.86953770281, 5573.14280143310],
      [0.00000202318, 2.45767790232, 6069.77675455340],
      [0.00000126225, 1.08295459501, 20.77539549240],
      [0.00000155516, 0.83306084617, 213.29909543800]
    ],
    [
      [6283.07584999140, 0.00000000000, 0.00000000000],
      [0.00206058863, 2.67823455808, 6283.07584999140],
      [0.00004303419, 2.63512233481, 12566.15169998280]
    ],
    [
      [0.00008721859, 1.07253635559, 6283.07584999140]
    ]
  ],
  [
    [
    ],
    [
      [0.00227777722, 3.41376620530, 6283.07584999140],
      [0.00003805678, 3.37063423795, 12566.15169998280]
    ]
  ],
  [
    [
      [1.00013988784, 0.00000000000, 0.00000000000],
      [0.01670699632, 3.09846350258, 6283.07584999140],
      [0.00013956024, 3.05524609456, 12566.15169998280],
      [0.00003083720, 5.19846674381, 77713.77146812050],
      [0.00001628463, 1.17387558054, 5753.38488489680],
      [0.00001575572, 2.84685214877, 7860.41939243920],
      [0.00000924799, 5.45292236722, 11506.76976979360],
      [0.00000542439, 4.56409151453, 3930.20969621960],
      [0.00000472110, 3.66100022149, 5884.92684658320]
    ],
    [
      [0.00103018607, 1.10748968172, 6283.07584999140],
      [0.00001721238, 1.06442300386, 12566.15169998280]
    ],
    [
      [0.00004359385, 5.78455133808, 6283.07584999140]
    ]
  ]
],

    # Mars
    [
  [
    [
      [6.20347711581, 0.00000000000, 0.00000000000],
      [0.18656368093, 5.05037100270, 3340.61242669980],
      [0.01108216816, 5.40099836344, 6681.22485339960],
      [0.00091798406, 5.75478744667, 10021.83728009940],
      [0.00027744987, 5.97049513147, 3.52311834900],
      [0.00010610235, 2.93958560338, 2281.23049651060],
      [0.00012315897, 0.84956094002, 2810.92146160520],
      [0.00008926784, 4.15697846427, 0.01725365220],
      [0.00008715691, 6.11005153139, 13362.44970679920],
      [0.00006797556, 0.36462229657, 398.14900340820],
      [0.00007774872, 3.33968761376, 5621.84292321040],
      [0.00003575078, 1.66186505710, 2544.31441988340],
      [0.00004161108, 0.22814971327, 2942.46342329160],
      [0.00003075252, 0.85696614132, 191.44826611160],
      [0.00002628117, 0.64806124465, 3337.08930835080],
      [0.00002937546, 6.07893711402, 0.06731030280],
      [0.00002389414, 5.03896442664, 796.29800681640],
      [0.00002579844, 0.02996736156, 3344.13554504880],
      [0.00001528141, 1.14979301996, 6151.53388830500],
      [0.00001798806, 0.65634057445, 529.69096509460],
      [0.00001264357, 3.62275122593, 5092.15195811580],
      [0.00001286228, 3.06796065034, 2146.16541647520],
      [0.00001546404, 2.91579701718, 1751.53953141600],
      [0.00001024902, 3.69334099279, 8962.45534991020],
      [0.00000891566, 0.18293837498, 16703.06213349900],
      [0.00000858759, 2.40093811940, 2914.01423582380],
      [0.00000832715, 2.46418619474, 3340.59517304760],
      [0.00000832720, 4.49495782139, 3340.62968035200],
      [0.00000712902, 3.66335473479, 1059.38193018920],
      [0.00000748723, 3.82248614017, 155.42039943420],
      [0.00000723861, 0.67497311481, 3738.76143010800],
      [0.00000635548, 2.92182225127, 8432.76438481560],
      [0.00000655162, 0.48864064125, 3127.31333126180],
      [0.00000550474, 3.81001042328, 0.98032106820],
      [0.00000552750, 4.47479317037, 1748.01641306700],
      [0.00000425966, 0.55364317304, 6283.07584999140],
      [0.00000415131, 0.49662285038, 213.29909543800],
      [0.00000472167, 3.62547124025, 1194.44701022460],
      [0.00000306551, 0.38052848348, 6684.74797174860],
      [0.00000312141, 0.99853944405, 6677.70173505060],
      [0.00000293198, 4.22131299634, 20.77539549240],
      [0.00000302375, 4.48618007156, 3532.06069281140],
      [0.00000274027, 0.54222167059, 3340.54511639700],
      [0.00000281079, 5.88163521788, 1349.86740965880],
      [0.00000231183, 1.28242156993, 3870.30339179440],
      [0.00000283602, 5.76885434940, 3149.16416058820],
      [0.00000236117, 5.75503217933, 3333.49887969900],
      [0.00000274033, 0.13372524985, 3340.67973700260],
      [0.00000299395, 2.78323740866, 6254.62666252360]
    ],
    [
      [3340.61242700512, 0.00000000000, 0.00000000000],
      [0.01457554523, 3.60433733236, 3340.61242669980],
      [0.00168414711, 3.92318567804, 6681.22485339960],
      [0.00020622975, 4.26108844583, 10021.83728009940],
      [0.00003452392, 4.73210393190, 3.52311834900],
      [0.00002586332, 4.60670058555, 13362.44970679920],
      [0.00000841535, 4.45864030426, 2281.23049651060]
    ],
    [
      [0.00058152577, 2.04961712429, 3340.61242669980],
      [0.00013459579, 2.45738706163, 6681.22485339960]
    ]
  ],
  [
    [
      [0.03197134986, 3.76832042431, 3340.61242669980],
      [0.00298033234, 4.10616996305, 6681.22485339960],
      [0.00289104742, 0.00000000000, 0.00000000000],
      [0.00031365539, 4.44651053090, 10021.83728009940],
      [0.00003484100, 4.78812549260, 13362.44970679920]
    ],
    [
      [0.00217310991, 6.04472194776, 3340.61242669980],
      [0.00020976948, 3.14159265359, 0.00000000000],
      [0.00012834709, 1.60810667915, 6681.22485339960]
    ]
  ],
  [
    [
      [1.53033488271, 0.00000000000, 0.00000000000],
      [0.14184953160, 3.47971283528, 3340.61242669980],
      [0.00660776362, 3.81783443019, 6681.22485339960],
      [0.00046179117, 4.15595316782, 10021.83728009940],
      [0.00008109733, 5.55958416318, 2810.92146160520],
      [0.00007485318, 1.77239078402, 5621.84292321040],
      [0.00005523191, 1.36436303770, 2281.23049651060],
      [0.00003825160, 4.49407183687, 13362.44970679920],
      [0.00002306537, 0.09081579001, 2544.31441988340],
      [0.00001999396, 5.36059617709, 3337.08930835080],
      [0.00002484394, 4.92545639920, 2942.46342329160],
      [0.00001960195, 4.74249437639, 3344.13554504880],
      [0.00001167119, 2.11260868341, 5092.15195811580],
      [0.00001102816, 5.00908403998, 398.14900340820],
      [0.00000899066, 4.40791133207, 529.69096509460],
      [0.00000992252, 5.83861961952, 6151.53388830500],
      [0.00000807354, 2.10217065501, 1059.38193018920],
      [0.00000797915, 3.44839203899, 796.29800681640],
      [0.00000740975, 1.49906336885, 2146.16541647520]
    ],
    [
      [0.01107433345, 2.03250524857, 3340.61242669980],
      [0.00103175887, 2.37071847807, 6681.22485339960],
      [0.00012877200, 0.00000000000, 0.00000000000],
      [0.00010815880, 2.70888095665, 10021.83728009940]
    ],
    [
      [0.00044242249, 0.47930604954, 3340.61242669980],
      [0.00008138042, 0.86998389204, 6681.22485339960]
    ]
  ]
],

    # Jupiter
    [
  [
    [
      [0.59954691494, 0.00000000000, 0.00000000000],
      [0.09695898719, 5.06191793158, 529.69096509460],
      [0.00573610142, 1.44406205629, 7.11354700080],
      [0.00306389205, 5.41734730184, 1059.38193018920],
      [0.00097178296, 4.14264726552, 632.78373931320],
      [0.00072903078, 3.64042916389, 522.57741809380],
      [0.00064263975, 3.41145165351, 103.09277421860],
      [0.00039806064, 2.29376740788, 419.48464387520],
      [0.00038857767, 1.27231755835, 316.39186965660],
      [0.00027964629, 1.78454591820, 536.80451209540],
      [0.00013589730, 5.77481040790, 1589.07289528380],
      [0.00008246349, 3.58227925840, 206.18554843720],
      [0.00008768704, 3.63000308199, 949.17560896980],
      [0.00007368042, 5.08101194270, 735.87651353180],
      [0.00006263150, 0.02497628807, 213.29909543800],
      [0.00006114062, 4.51319998626, 1162.47470440780],
      [0.00004905396, 1.32084470588, 110.20632121940],
      [0.00005305285, 1.30671216791, 14.22709400160],
      [0.00005305441, 4.18625634012, 1052.26838318840],
      [0.00004647248, 4.69958103684, 3.93215326310],
      [0.00003045023, 4.31676431084, 426.59819087600],
      [0.00002609999, 1.56667394063, 846.08283475120],
      [0.00002028191, 1.06376530715, 3.18139373770],
      [0.00001764763, 2.14148655117, 1066.49547719000],
      [0.00001722972, 3.88036268267, 1265.56747862640],
      [0.00001920945, 0.97168196472, 639.89728631400],
      [0.00001633223, 3.58201833555, 515.46387109300],
      [0.00001431999, 4.29685556046, 625.67019231240],
      [0.00000973272, 4.09764549134, 95.97922721780]
    ],
    [
      [529.69096508814, 0.00000000000, 0.00000000000],
      [0.00489503243, 4.22082939470, 529.69096509460],
      [0.00228917222, 6.02646855621, 7.11354700080],
      [0.00030099479, 4.54540782858, 1059.38193018920],
      [0.00020720920, 5.45943156902, 522.57741809380],
      [0.00012103653, 0.16994816098, 536.80451209540],
      [0.00006067987, 4.42422292017, 103.09277421860],
      [0.00005433968, 3.98480737746, 419.48464387520],
      [0.00004237744, 5.89008707199, 14.22709400160]
    ],
    [
      [0.00047233601, 4.32148536482, 7.11354700080],
      [0.00030649436, 2.92977788700, 529.69096509460],
      [0.00014837605, 3.14159265359, 0.00000000000]
    ]
  ],
  [
    [
      [0.02268615702, 3.55852606721, 529.69096509460],
      [0.00109971634, 3.90809347197, 1059.38193018920],
      [0.00110090358, 0.00000000000, 0.00000000000],
      [0.00008101428, 3.60509572885, 522.57741809380],
      [0.00006043996, 4.25883108339, 1589.07289528380],
      [0.00006437782, 0.30627119215, 536.80451209540]
    ],
    [
      [0.00078203446, 1.52377859742, 529.69096509460]
    ]
  ],
  [
    [
      [5.20887429326, 0.00000000000, 0.00000000000],
      [0.25209327119, 3.49108639871, 529.69096509460],
      [0.00610599976, 3.84115365948, 1059.38193018920],
      [0.00282029458, 2.57419881293, 632.78373931320],
      [0.00187647346, 2.07590383214, 522.57741809380],
      [0.00086792905, 0.71001145545, 419.48464387520],
      [0.00072062974, 0.21465724607, 536.80451209540],
      [0.00065517248, 5.97995884790, 316.39186965660],
      [0.00029134542, 1.67759379655, 103.09277421860],
      [0.00030135335, 2.16132003734, 949.17560896980],
      [0.00023453271, 3.54023522184, 735.87651353180],
      [0.00022283743, 4.19362594399, 1589.07289528380],
      [0.00023947298, 0.27458037480, 7.11354700080],
      [0.00013032614, 2.96042965363, 1162.47470440780],
      [0.00009703360, 1.90669633585, 206.18554843720],
      [0.00012749023, 2.71550286592, 1052.26838318840]
    ],
    [
      [0.01271801520, 2.64937512894, 529.69096509460],
      [0.00061661816, 3.00076460387, 1059.38193018920],
      [0.00053443713, 3.89717383175, 522.57741809380],
      [0.00031185171, 4.88276958012, 536.80451209540],
      [0.00041390269, 0.00000000000, 0.00000000000]
    ]
  ]
],

    # Saturn
    [
  [
    [
      [0.87401354025, 0.00000000000, 0.00000000000],
      [0.11107659762, 3.96205090159, 213.29909543800],
      [0.01414150957, 4.58581516874, 7.11354700080],
      [0.00398379389, 0.52112032699, 206.18554843720],
      [0.00350769243, 3.30329907896, 426.59819087600],
      [0.00206816305, 0.24658372002, 103.09277421860],
      [0.00079271300, 3.84007056878, 220.41264243880],
      [0.00023990355, 4.66976924553, 110.20632121940],
      [0.00016573588, 0.43719228296, 419.48464387520],
      [0.00014906995, 5.76903183869, 316.39186965660],
      [0.00015820290, 0.93809155235, 632.78373931320],
      [0.00014609559, 1.56518472000, 3.93215326310],
      [0.00013160301, 4.44891291899, 14.22709400160],
      [0.00015053543, 2.71669915667, 639.89728631400],
      [0.00013005299, 5.98119023644, 11.04570026390],
      [0.00010725067, 3.12939523827, 202.25339517410],
      [0.00005863206, 0.23656938524, 529.69096509460],
      [0.00005227757, 4.20783365759, 3.18139373770],
      [0.00006126317, 1.76328667907, 277.03499374140],
      [0.00005019687, 3.17787728405, 433.71173787680],
      [0.00004592550, 0.61977744975, 199.07200143640],
      [0.00004005867, 2.24479718502, 63.73589830340],
      [0.00002953796, 0.98280366998, 95.97922721780],
      [0.00003873670, 3.22283226966, 138.51749687070],
      [0.00002461186, 2.03163875071, 735.87651353180],
      [0.00003269484, 0.77492638211, 949.17560896980],
      [0.00001758145, 3.26580109940, 522.57741809380],
      [0.00001640172, 5.50504453050, 846.08283475120],
      [0.00001391327, 4.02333150505, 323.50541665740],
      [0.00001580648, 4.37265307169, 309.27832265580],
      [0.00001123498, 2.83726798446, 415.55249061210],
      [0.00001017275, 3.71700135395, 227.52618943960],
      [0.00000848642, 3.19150170830, 209.36694217490]
    ],
    [
      [213.29909521690, 0.00000000000, 0.00000000000],
      [0.01297370862, 1.82834923978, 213.29909543800],
      [0.00564345393, 2.88499717272, 7.11354700080],
      [0.00093734369, 1.06311793502, 426.59819087600],
      [0.00107674962, 2.27769131009, 206.18554843720],
      [0.00040244455, 2.04108104671, 220.41264243880],
      [0.00019941774, 1.27954390470, 103.09277421860],
      [0.00010511678, 2.74880342130, 14.22709400160],
      [0.00006416106, 0.38238295041, 639.89728631400],
      [0.00004848994, 2.43037610229, 419.48464387520],
      [0.00004056892, 2.92133209468, 110.20632121940],
      [0.00003768635, 3.64965330780, 3.93215326310]
    ],
    [
      [0.00116441330, 1.17988132879, 7.11354700080],
      [0.00091841837, 0.07325195840, 213.29909543800],
      [0.00036661728, 0.00000000000, 0.00000000000],
      [0.00015274496, 4.06493179167, 206.18554843720]
    ]
  ],
  [
    [
      [0.04330678039, 3.60284428399, 213.29909543800],
      [0.00240348302, 2.85238489373, 426.59819087600],
      [0.00084745939, 0.00000000000, 0.00000000000],
      [0.00030863357, 3.48441504555, 220.41264243880],
      [0.00034116062, 0.57297307557, 206.18554843720],
      [0.00014734070, 2.11846596715, 639.89728631400],
      [0.00009916667, 5.79003188904, 419.48464387520],
      [0.00006993564, 4.73604689720, 7.11354700080],
      [0.00004807588, 5.43305312061, 316.39186965660]
    ],
    [
      [0.00198927992, 4.93901017903, 213.29909543800],
      [0.00036947916, 3.14159265359, 0.00000000000],
      [0.00017966989, 0.51979431110, 426.59819087600]
    ]
  ],
  [
    [
      [9.55758135486, 0.00000000000, 0.00000000000],
      [0.52921382865, 2.39226219573, 213.29909543800],
      [0.01873679867, 5.23549604660, 206.18554843720],
      [0.01464663929, 1.64763042902, 426.59819087600],
      [0.00821891141, 5.93520042303, 316.39186965660],
      [0.00547506923, 5.01532618980, 103.09277421860],
      [0.00371684650, 2.27114821115, 220.41264243880],
      [0.00361778765, 3.13904301847, 7.11354700080],
      [0.00140617506, 5.70406606781, 632.78373931320],
      [0.00108974848, 3.29313390175, 110.20632121940],
      [0.00069006962, 5.94099540992, 419.48464387520],
      [0.00061053367, 0.94037691801, 639.89728631400],
      [0.00048913294, 1.55733638681, 202.25339517410],
      [0.00034143772, 0.19519102597, 277.03499374140],
      [0.00032401773, 5.47084567016, 949.17560896980],
      [0.00020936596, 0.46349251129, 735.87651353180]
    ],
    [
      [0.06182981340, 0.25843511480, 213.29909543800],
      [0.00506577242, 0.71114625261, 206.18554843720],
      [0.00341394029, 5.79635741658, 426.59819087600],
      [0.00188491195, 0.47215589652, 220.41264243880],
      [0.00186261486, 3.14159265359, 0.00000000000],
      [0.00143891146, 1.40744822888, 7.11354700080]
    ],
    [
      [0.00436902572, 4.78671677509, 213.29909543800]
    ]
  ]
],

    # Uranus
    [
  [
    [
      [5.48129294297, 0.00000000000, 0.00000000000],
      [0.09260408234, 0.89106421507, 74.78159856730],
      [0.01504247898, 3.62719260920, 1.48447270830],
      [0.00365981674, 1.89962179044, 73.29712585900],
      [0.00272328168, 3.35823706307, 149.56319713460],
      [0.00070328461, 5.39254450063, 63.73589830340],
      [0.00068892678, 6.09292483287, 76.26607127560],
      [0.00061998615, 2.26952066061, 2.96894541660],
      [0.00061950719, 2.85098872691, 11.04570026390],
      [0.00026468770, 3.14152083966, 71.81265315070],
      [0.00025710476, 6.11379840493, 454.90936652730],
      [0.00021078850, 4.36059339067, 148.07872442630],
      [0.00017818647, 1.74436930289, 36.64856292950],
      [0.00014613507, 4.73732166022, 3.93215326310],
      [0.00011162509, 5.82681796350, 224.34479570190],
      [0.00010997910, 0.48865004018, 138.51749687070],
      [0.00009527478, 2.95516862826, 35.16409022120],
      [0.00007545601, 5.23626582400, 109.94568878850],
      [0.00004220241, 3.23328220918, 70.84944530420],
      [0.00004051900, 2.27755017300, 151.04766984290],
      [0.00003354596, 1.06549007380, 4.45341812490],
      [0.00002926718, 4.62903718891, 9.56122755560],
      [0.00003490340, 5.48306144511, 146.59425171800],
      [0.00003144069, 4.75199570434, 77.75054398390],
      [0.00002922333, 5.35235361027, 85.82729883120],
      [0.00002272788, 4.36600400036, 70.32818044240],
      [0.00002051219, 1.51773566586, 0.11187458460],
      [0.00002148602, 0.60745949945, 38.13303563780],
      [0.00001991643, 4.92437588682, 277.03499374140],
      [0.00001376226, 2.04283539351, 65.22037101170],
      [0.00001666902, 3.62744066769, 380.12776796000],
      [0.00001284107, 3.11347961505, 202.25339517410],
      [0.00001150429, 0.93343589092, 3.18139373770],
      [0.00001533221, 2.58594681212, 52.69019803950],
      [0.00001281604, 0.54271272721, 222.86032299360],
      [0.00001372139, 4.19641530878, 111.43016149680],
      [0.00001221029, 0.19900650030, 108.46121608020],
      [0.00000946181, 1.19253165736, 127.47179660680],
      [0.00001150989, 4.17898916639, 33.67961751290]
    ],
    [
      [74.78159860910, 0.00000000000, 0.00000000000],
      [0.00154332863, 5.24158770553, 74.78159856730],
      [0.00024456474, 1.71260334156, 1.48447270830],
      [0.00009258442, 0.42829732350, 11.04570026390],
      [0.00008265977, 1.50218091379, 63.73589830340],
      [0.00009150160, 1.41213765216, 149.56319713460]
    ]
  ],
  [
    [
      [0.01346277648, 2.61877810547, 74.78159856730],
      [0.00062341400, 5.08111189648, 149.56319713460],
      [0.00061601196, 3.14159265359, 0.00000000000],
      [0.00009963722, 1.61603805646, 76.26607127560],
      [0.00009926160, 0.57630380333, 73.29712585900]
    ],
    [
      [0.00034101978, 0.01321929936, 74.78159856730]
    ]
  ],
  [
    [
      [19.21264847206, 0.00000000000, 0.00000000000],
      [0.88784984413, 5.60377527014, 74.78159856730],
      [0.03440836062, 0.32836099706, 73.29712585900],
      [0.02055653860, 1.78295159330, 149.56319713460],
      [0.00649322410, 4.52247285911, 76.26607127560],
      [0.00602247865, 3.86003823674, 63.73589830340],
      [0.00496404167, 1.40139935333, 454.90936652730],
      [0.00338525369, 1.58002770318, 138.51749687070],
      [0.00243509114, 1.57086606044, 71.81265315070],
      [0.00190522303, 1.99809394714, 1.48447270830],
      [0.00161858838, 2.79137786799, 148.07872442630],
      [0.00143706183, 1.38368544947, 11.04570026390],
      [0.00093192405, 0.17437220467, 36.64856292950],
      [0.00071424548, 4.24509236074, 224.34479570190],
      [0.00089806014, 3.66105364565, 109.94568878850],
      [0.00039009723, 1.66971401684, 70.84944530420],
      [0.00046677296, 1.39976401694, 35.16409022120],
      [0.00039025624, 3.36234773834, 277.03499374140],
      [0.00036755274, 3.88649278513, 146.59425171800],
      [0.00030348723, 0.70100838798, 151.04766984290],
      [0.00029156413, 3.18056336700, 77.75054398390]
    ],
    [
      [0.01479896629, 3.67205697578, 74.78159856730]
    ]
  ]
],

    # Neptune
    [
  [
    [
      [5.31188633046, 0.00000000000, 0.00000000000],
      [0.01798475530, 2.90101273890, 38.13303563780],
      [0.01019727652, 0.48580922867, 1.48447270830],
      [0.00124531845, 4.83008090676, 36.64856292950],
      [0.00042064466, 5.41054993053, 2.96894541660],
      [0.00037714584, 6.09221808686, 35.16409022120],
      [0.00033784738, 1.24488874087, 76.26607127560],
      [0.00016482741, 0.00007727998, 491.55792945680],
      [0.00009198584, 4.93747051954, 39.61750834610],
      [0.00008994250, 0.27462171806, 175.16605980020]
    ],
    [
      [38.13303563957, 0.00000000000, 0.00000000000],
      [0.00016604172, 4.86323329249, 1.48447270830],
      [0.00015744045, 2.27887427527, 38.13303563780]
    ]
  ],
  [
    [
      [0.03088622933, 1.44104372644, 38.13303563780],
      [0.00027780087, 5.91271884599, 76.26607127560],
      [0.00027623609, 0.00000000000, 0.00000000000],
      [0.00015355489, 2.52123799551, 36.64856292950],
      [0.00015448133, 3.50877079215, 39.61750834610]
    ]
  ],
  [
    [
      [30.07013205828, 0.00000000000, 0.00000000000],
      [0.27062259632, 1.32999459377, 38.13303563780],
      [0.01691764014, 3.25186135653, 36.64856292950],
      [0.00807830553, 5.18592878704, 1.48447270830],
      [0.00537760510, 4.52113935896, 35.16409022120],
      [0.00495725141, 1.57105641650, 491.55792945680],
      [0.00274571975, 1.84552258866, 175.16605980020]
    ]
  ]
],
]

def _CalcVsop(model, time):
    spher = []
    t = time.tt / 365250.0
    for formula in model:
        tpower = 1.0
        coord = 0.0
        for series in formula:
            coord += tpower * sum(A * math.cos(B + C*t) for (A, B, C) in series)
            tpower *= t
        spher.append(coord)

    # Convert spherical coordinates to ecliptic cartesian coordinates.
    r_coslat = spher[2] * math.cos(spher[1])
    ex = r_coslat * math.cos(spher[0])
    ey = r_coslat * math.sin(spher[0])
    ez = spher[2] * math.sin(spher[1])

    # Convert ecliptic cartesian coordinates to equatorial cartesian coordinates.
    vx = ex + 0.000000440360*ey - 0.000000190919*ez
    vy = -0.000000479966*ex + 0.917482137087*ey - 0.397776982902*ez
    vz = 0.397776982902*ey + 0.917482137087*ez
    return Vector(vx, vy, vz, time)

def _CalcEarth(time):
    return _CalcVsop(_vsop[Body.Earth], time)

# END VSOP
#----------------------------------------------------------------------------
# BEGIN CHEBYSHEV

_pluto = [
{ 'tt':-109573.500000, 'ndays':26141.000000, 'coeff':[
    [-30.303124711144, -18.980368465705, 3.206649343866],
    [20.092745278347, -27.533908687219, -14.641121965990],
    [9.137264744925, 6.513103657467, -0.720732357468],
    [-1.201554708717, 2.149917852301, 1.032022293526],
    [-0.566068170022, -0.285737361191, 0.081379987808],
    [0.041678527795, -0.143363105040, -0.057534475984],
    [0.041087908142, 0.007911321580, -0.010270655537],
    [0.001611769878, 0.011409821837, 0.003679980733],
    [-0.002536458296, -0.000145632543, 0.000949924030],
    [0.001167651969, -0.000049912680, 0.000115867710],
    [-0.000196953286, 0.000420406270, 0.000110147171],
    [0.001073825784, 0.000442658285, 0.000146985332],
    [-0.000906160087, 0.001702360394, 0.000758987924],
    [-0.001467464335, -0.000622191266, -0.000231866243],
    [-0.000008986691, 0.000004086384, 0.000001442956],
    [-0.001099078039, -0.000544633529, -0.000205534708],
    [0.001259974751, -0.002178533187, -0.000965315934],
    [0.001695288316, 0.000768480768, 0.000287916141],
    [-0.001428026702, 0.002707551594, 0.001195955756]]
},
{ 'tt':-83432.500000, 'ndays':26141.000000, 'coeff':[
    [67.049456204563, -9.279626603192, -23.091941092128],
    [14.860676672314, 26.594121136143, 3.819668867047],
    [-6.254409044120, 1.408757903538, 2.323726101433],
    [0.114416381092, -0.942273228585, -0.328566335886],
    [0.074973631246, 0.106749156044, 0.010806547171],
    [-0.018627741964, -0.009983491157, 0.002589955906],
    [0.006167206174, -0.001042430439, -0.001521881831],
    [-0.000471293617, 0.002337935239, 0.001060879763],
    [-0.000240627462, -0.001380351742, -0.000546042590],
    [0.001872140444, 0.000679876620, 0.000240384842],
    [-0.000334705177, 0.000693528330, 0.000301138309],
    [0.000796124758, 0.000653183163, 0.000259527079],
    [-0.001276116664, 0.001393959948, 0.000629574865],
    [-0.001235158458, -0.000889985319, -0.000351392687],
    [-0.000019881944, 0.000048339979, 0.000021342186],
    [-0.000987113745, -0.000748420747, -0.000296503569],
    [0.001721891782, -0.001893675502, -0.000854270937],
    [0.001505145187, 0.001081653337, 0.000426723640],
    [-0.002019479384, 0.002375617497, 0.001068258925]]
},
{ 'tt':-57291.500000, 'ndays':26141.000000, 'coeff':[
    [46.038290912405, 73.773759757856, 9.148670950706],
    [-22.354364534703, 10.217143138926, 9.921247676076],
    [-2.696282001399, -4.440843715929, -0.572373037840],
    [0.385475818800, -0.287872688575, -0.205914693555],
    [0.020994433095, 0.004256602589, -0.004817361041],
    [0.003212255378, 0.000574875698, -0.000764464370],
    [-0.000158619286, -0.001035559544, -0.000535612316],
    [0.000967952107, -0.000653111849, -0.000292019750],
    [0.001763494906, -0.000370815938, -0.000224698363],
    [0.001157990330, 0.001849810828, 0.000759641577],
    [-0.000883535516, 0.000384038162, 0.000191242192],
    [0.000709486562, 0.000655810827, 0.000265431131],
    [-0.001525810419, 0.001126870468, 0.000520202001],
    [-0.000983210860, -0.001116073455, -0.000456026382],
    [-0.000015655450, 0.000069184008, 0.000029796623],
    [-0.000815102021, -0.000900597010, -0.000365274209],
    [0.002090300438, -0.001536778673, -0.000709827438],
    [0.001234661297, 0.001342978436, 0.000545313112],
    [-0.002517963678, 0.001941826791, 0.000893859860]]
},
{ 'tt':-31150.500000, 'ndays':26141.000000, 'coeff':[
    [-39.074661990988, 30.963513412373, 21.431709298065],
    [-12.033639281924, -31.693679132310, -6.263961539568],
    [7.233936758611, -3.979157072767, -3.421027935569],
    [1.383182539917, 1.090729793400, -0.076771771448],
    [-0.009894394996, 0.313614402007, 0.101180677344],
    [-0.055459383449, 0.031782406403, 0.026374448864],
    [-0.011074105991, -0.007176759494, 0.001896208351],
    [-0.000263363398, -0.001145329444, 0.000215471838],
    [0.000405700185, -0.000839229891, -0.000418571366],
    [0.001004921401, 0.001135118493, 0.000406734549],
    [-0.000473938695, 0.000282751002, 0.000114911593],
    [0.000528685886, 0.000966635293, 0.000401955197],
    [-0.001838869845, 0.000806432189, 0.000394594478],
    [-0.000713122169, -0.001334810971, -0.000554511235],
    [0.000006449359, 0.000060730000, 0.000024513230],
    [-0.000596025142, -0.000999492770, -0.000413930406],
    [0.002364904429, -0.001099236865, -0.000528480902],
    [0.000907458104, 0.001537243912, 0.000637001965],
    [-0.002909908764, 0.001413648354, 0.000677030924]]
},
{ 'tt':-5009.500000, 'ndays':26141.000000, 'coeff':[
    [23.380075041204, -38.969338804442, -19.204762094135],
    [33.437140696536, 8.735194448531, -7.348352917314],
    [-3.127251304544, 8.324311848708, 3.540122328502],
    [-1.491354030154, -1.350371407475, 0.028214278544],
    [0.361398480996, -0.118420687058, -0.145375605480],
    [-0.011771350229, 0.085880588309, 0.030665997197],
    [-0.015839541688, -0.014165128211, 0.000523465951],
    [0.004213218926, -0.001426373728, -0.001906412496],
    [0.001465150002, 0.000451513538, 0.000081936194],
    [0.000640069511, 0.001886692235, 0.000884675556],
    [-0.000883554940, 0.000301907356, 0.000127310183],
    [0.000245524038, 0.000910362686, 0.000385555148],
    [-0.001942010476, 0.000438682280, 0.000237124027],
    [-0.000425455660, -0.001442138768, -0.000607751390],
    [0.000004168433, 0.000033856562, 0.000013881811],
    [-0.000337920193, -0.001074290356, -0.000452503056],
    [0.002544755354, -0.000620356219, -0.000327246228],
    [0.000534534110, 0.001670320887, 0.000702775941],
    [-0.003169380270, 0.000816186705, 0.000427213817]]
},
{ 'tt':21131.500000, 'ndays':26141.000000, 'coeff':[
    [74.130449310804, 43.372111541004, -8.799489207171],
    [-8.705941488523, 23.344631690845, 9.908006472122],
    [-4.614752911564, -2.587334376729, 0.583321715294],
    [0.316219286624, -0.395448970181, -0.219217574801],
    [0.004593734664, 0.027528474371, 0.007736197280],
    [-0.001192268851, -0.004987723997, -0.001599399192],
    [0.003051998429, -0.001287028653, -0.000780744058],
    [0.001482572043, 0.001613554244, 0.000635747068],
    [0.000581965277, 0.000788286674, 0.000315285159],
    [-0.000311830730, 0.001622369930, 0.000714817617],
    [-0.000711275723, -0.000160014561, -0.000050445901],
    [0.000177159088, 0.001032713853, 0.000435835541],
    [-0.002032280820, 0.000144281331, 0.000111910344],
    [-0.000148463759, -0.001495212309, -0.000635892081],
    [-0.000009629403, -0.000013678407, -0.000006187457],
    [-0.000061196084, -0.001119783520, -0.000479221572],
    [0.002630993795, -0.000113042927, -0.000112115452],
    [0.000132867113, 0.001741417484, 0.000743224630],
    [-0.003293498893, 0.000182437998, 0.000158073228]]
},
{ 'tt':47272.500000, 'ndays':26141.000000, 'coeff':[
    [-5.727994625506, 71.194823351703, 23.946198176031],
    [-26.767323214686, -12.264949302780, 4.238297122007],
    [0.890596204250, -5.970227904551, -2.131444078785],
    [0.808383708156, -0.143104108476, -0.288102517987],
    [0.089303327519, 0.049290470655, -0.010970501667],
    [0.010197195705, 0.012879721400, 0.001317586740],
    [0.001795282629, 0.004482403780, 0.001563326157],
    [-0.001974716105, 0.001278073933, 0.000652735133],
    [0.000906544715, -0.000805502229, -0.000336200833],
    [0.000283816745, 0.001799099064, 0.000756827653],
    [-0.000784971304, 0.000123081220, 0.000068812133],
    [-0.000237033406, 0.000980100466, 0.000427758498],
    [-0.001976846386, -0.000280421081, -0.000072417045],
    [0.000195628511, -0.001446079585, -0.000624011074],
    [-0.000044622337, -0.000035865046, -0.000013581236],
    [0.000204397832, -0.001127474894, -0.000488668673],
    [0.002625373003, 0.000389300123, 0.000102756139],
    [-0.000277321614, 0.001732818354, 0.000749576471],
    [-0.003280537764, -0.000457571669, -0.000116383655]]
}]

def _ChebScale(t_min, t_max, t):
    return (2*t - (t_max + t_min)) / (t_max - t_min)

def _CalcChebyshev(model, time):
    # Search for a record that overlaps the given time value.
    for record in model:
        x = _ChebScale(record['tt'], record['tt'] + record['ndays'], time.tt)
        if -1 <= x <= +1:
            coeff = record['coeff']
            pos = []
            for d in range(3):
                p0 = 1
                sum = coeff[0][d]
                p1 = x
                sum += coeff[1][d] * p1
                for k in range(2, len(coeff)):
                    p2 = (2 * x * p1) - p0
                    sum += coeff[k][d] * p2
                    p0 = p1
                    p1 = p2
                pos.append(sum - coeff[0][d]/2)
            return Vector(pos[0], pos[1], pos[2], time)
    raise Error('Cannot extrapolate Chebyshev model for given Terrestrial Time: {}'.format(time.tt))

# END CHEBYSHEV
#----------------------------------------------------------------------------
# BEGIN Search

def _QuadInterp(tm, dt, fa, fm, fb):
    Q = (fb + fa)/2 - fm
    R = (fb - fa)/2
    S = fm

    if Q == 0:
        # This is a line, not a parabola.
        if R == 0:
            # This is a HORIZONTAL line... can't make progress!
            return None
        x = -S / R
        if not (-1 <= x <= +1):
            return None  # out of bounds
    else:
        # It really is a parabola. Find roots x1, x2.
        u = R*R - 4*Q*S
        if u <= 0:
            return None
        ru = math.sqrt(u)
        x1 = (-R + ru) / (2 * Q)
        x2 = (-R - ru) / (2 * Q)

        if -1 <= x1 <= +1:
            if -1 <= x2 <= +1:
                # Two solutions... so parabola intersects twice.
                return None
            x = x1
        elif -1 <= x2 <= +1:
            x = x2
        else:
            return None

    t = tm + x*dt
    df_dt = (2*Q*x + R) / dt
    return (x, t, df_dt)

def Search(func, context, t1, t2, dt_tolerance_seconds):
    """Searches for a time at which a function's value increases through zero.

    Certain astronomy calculations involve finding a time when an event occurs.
    Often such events can be defined as the root of a function:
    the time at which the function's value becomes zero.

    `Search` finds the *ascending root* of a function: the time at which
    the function's value becomes zero while having a positive slope. That is, as time increases,
    the function transitions from a negative value, through zero at a specific moment,
    to a positive value later. The goal of the search is to find that specific moment.

    The search function is specified by two parameters: `func` and `context`.
    The `func` parameter is a function itself that accepts a time
    and a context containing any other arguments needed to evaluate the function.
    The `context` parameter supplies that context for the given search.
    As an example, a caller may wish to find the moment a celestial body reaches a certain
    ecliptic longitude. In that case, the caller might create a type (class, tuple, whatever)
    that contains a #Body member to specify the body and a numeric value to hold the target longitude.
    A different function might use a completely different context type.

    Every time it is called, `func` returns a `float` value or it raises an exception.
    If `func` raises an exception, the search immediately fails and the exception is
    propagated back to the caller.
    Otherwise, the search proceeds until it either finds the ascending root or fails for some reason.

    The search calls `func` repeatedly to rapidly narrow in on any ascending
    root within the time window specified by `t1` and `t2`. The search never
    reports a solution outside this time window.

    `Search` uses a combination of bisection and quadratic interpolation
    to minimize the number of function calls. However, it is critical that the
    supplied time window be small enough that there cannot be more than one root
    (ascedning or descending) within it; otherwise the search can fail.
    Beyond that, it helps to make the time window as small as possible, ideally
    such that the function itself resembles a smooth parabolic curve within that window.

    If an ascending root is not found, or more than one root
    (ascending and/or descending) exists within the window `t1`..`t2`,
    `Search` will return `None` to indicate a normal search failure.

    If the search does not converge within 20 iterations, it will raise
    an #Error exception.

    Parameters
    ----------
    func : function(context, Time)
        A function that takes an arbitrary context parameter and a #Time parameter.
        Returns a float value.  See remarks above for more details.

    context : object
        An arbitrary data structure needed to be passed to the function `func`
        every time it is called.

    t1 : float
        The lower time bound of the search window.
        See remarks above for more details.

    t2 : float
        The upper time bound of the search window.
        See remarks above for more details.

    dt_tolerance_seconds : float
        Specifies an amount of time in seconds within which a bounded ascending root
        is considered accurate enough to stop. A typical value is 1 second.

    Returns
    -------
    #Time or `None`
        If the search is successful, returns a #Time object that is within
        `dt_tolerance_seconds` of an ascending root.
        In this case, the returned time value will always be within the
        inclusive range [`t1`, `t2`].
        If there is no ascending root, or there is more than one ascending root,
        the function returns `None`.

    """
    dt_days = abs(dt_tolerance_seconds / _SECONDS_PER_DAY)
    f1 = func(context, t1)
    f2 = func(context, t2)
    iter = 0
    iter_limit = 20
    calc_fmid = True
    while True:
        iter += 1
        if iter > iter_limit:
            raise Error('Excessive iteration in Search')

        dt = (t2.tt - t1.tt) / 2.0
        tmid = t1.AddDays(dt)
        if abs(dt) < dt_days:
            # We are close enough to the event to stop the search.
            return tmid

        if calc_fmid:
            fmid = func(context, tmid)
        else:
            # We already have the correct value of fmid from the previous loop.
            calc_fmid = True

        # Quadratic interpolation:
        # Try to find a parabola that passes through the 3 points we have sampled:
        # (t1,f1), (tmid,fmid), (t2,f2).
        q = _QuadInterp(tmid.ut, t2.ut - tmid.ut, f1, fmid, f2)
        if q:
            (q_x, q_ut, q_df_dt) = q
            tq = Time(q_ut)
            fq = func(context, tq)
            if q_df_dt != 0.0:
                dt_guess = abs(fq / q_df_dt)
                if dt_guess < dt_days:
                    # The estimated time error is small enough that we can quit now.
                    return tq

                # Try guessing a tighter boundary with the interpolated root at the center.
                dt_guess *= 1.2
                if dt_guess < dt / 10.0:
                    tleft = tq.AddDays(-dt_guess)
                    tright = tq.AddDays(+dt_guess)
                    if (tleft.ut - t1.ut)*(tleft.ut - t2.ut) < 0.0:
                        if (tright.ut - t1.ut)*(tright.ut - t2.ut) < 0.0:
                            fleft = func(context, tleft)
                            fright = func(context, tright)
                            if fleft < 0.0 and fright >= 0.0:
                                f1 = fleft
                                f2 = fright
                                t1 = tleft
                                t2 = tright
                                fmid = fq
                                calc_fmid = False
                                continue

        # Quadratic interpolation attempt did not work out.
        # Just divide the region in two parts and pick whichever one appears to contain a root.
        if f1 < 0.0 and fmid >= 0.0:
            t2 = tmid
            f2 = fmid
            continue

        if fmid < 0.0 and f2 >= 0.0:
            t1 = tmid
            f1 = fmid
            continue

        # Either there is no ascending zero-crossing in this range
        # or the search window is too wide (more than one zero-crossing).
        return None

# END Search
#----------------------------------------------------------------------------

def HelioVector(body, time):
    """Calculates heliocentric Cartesian coordinates of a body in the J2000 equatorial system.

    This function calculates the position of the given celestial body as a vector,
    using the center of the Sun as the origin.  The result is expressed as a Cartesian
    vector in the J2000 equatorial system: the coordinates are based on the mean equator
    of the Earth at noon UTC on 1 January 2000.

    The position is not corrected for light travel time or aberration.
    This is different from the behavior of #GeoVector.

    If given an invalid value for `body`, or the body is `Body.Pluto` and `time` is outside
    the year range 1700..2200, this function raise an exception.

    Parameters
    ----------
    body : Body
        The celestial body whose heliocentric position is to be calculated:
        The Sun, Moon, or any of the planets.
    time : Time
        The time at which to calculate the heliocentric position.

    Returns
    -------
    #Vector
        A heliocentric position vector of the center of the given body
        at the given time.
    """
    if body == Body.Pluto:
        return _CalcChebyshev(_pluto, time)

    if 0 <= body <= len(_vsop):
        return _CalcVsop(_vsop[body], time)

    if body == Body.Sun:
        return Vector(0.0, 0.0, 0.0, time)

    if body == Body.Moon:
        e = _CalcEarth(time)
        m = GeoMoon(time)
        return Vector(e.x+m.x, e.y+m.y, e.z+m.z, time)

    raise InvalidBodyError()


def GeoVector(body, time, aberration):
    """Calculates geocentric Cartesian coordinates of a body in the J2000 equatorial system.

    This function calculates the position of the given celestial body as a vector,
    using the center of the Earth as the origin.  The result is expressed as a Cartesian
    vector in the J2000 equatorial system: the coordinates are based on the mean equator
    of the Earth at noon UTC on 1 January 2000.

    If given an invalid value for `body`, or the body is `Body.Pluto` and the `time` is outside
    the year range 1700..2200, this function will raise an exception.

    Unlike #HelioVector, this function always corrects for light travel time.
    This means the position of the body is "back-dated" by the amount of time it takes
    light to travel from that body to an observer on the Earth.

    Also, the position can optionally be corrected for
    [aberration](https://en.wikipedia.org/wiki/Aberration_of_light), an effect
    causing the apparent direction of the body to be shifted due to transverse
    movement of the Earth with respect to the rays of light coming from that body.

    Parameters
    ----------
    body : Body
        A body for which to calculate a heliocentric position: the Sun, Moon, or any of the planets.
    time : Time
        The date and time for which to calculate the position.
    aberration : bool
        A boolean value indicating whether to correct for aberration.

    Returns
    -------
    #Vector
        A geocentric position vector of the center of the given body.
    """
    if body == Body.Moon:
        return GeoMoon(time)

    if body == Body.Earth:
        return Vector(0.0, 0.0, 0.0, time)

    if not aberration:
        # No aberration, so calculate Earth's position once, at the time of observation.
        earth = _CalcEarth(time)

    # Correct for light-travel time, to get position of body as seen from Earth's center.
    ltime = time
    for iter in range(10):
        h = HelioVector(body, ltime)
        if aberration:
            # Include aberration, so make a good first-order approximation
            # by backdating the Earth's position also.
            # This is confusing, but it works for objects within the Solar System
            # because the distance the Earth moves in that small amount of light
            # travel time (a few minutes to a few hours) is well approximated
            # by a line segment that substends the angle seen from the remote
            # body viewing Earth. That angle is pretty close to the aberration
            # angle of the moving Earth viewing the remote body.
            # In other words, both of the following approximate the aberration angle:
            #    (transverse distance Earth moves) / (distance to body)
            #    (transverse speed of Earth) / (speed of light).
            earth = _CalcEarth(ltime)

        geo = Vector(h.x-earth.x, h.y-earth.y, h.z-earth.z, time)
        if body == Body.Sun:
            # The Sun's heliocentric coordinates are always (0,0,0). No need to correct.
            return geo

        ltime2 = time.AddDays(-geo.Length() / _C_AUDAY)
        dt = abs(ltime2.tt - ltime.tt)
        if dt < 1.0e-9:
            return geo

        ltime = ltime2

    raise Error('Light-travel time solver did not converge: dt={}'.format(dt))


def Equator(body, time, observer, ofdate, aberration):
    """Calculates equatorial coordinates of a celestial body as seen by an observer on the Earth's surface.

    Calculates topocentric equatorial coordinates in one of two different systems:
    J2000 or true-equator-of-date, depending on the value of the `ofdate` parameter.
    Equatorial coordinates include right ascension, declination, and distance in astronomical units.

    This function corrects for light travel time: it adjusts the apparent location
    of the observed body based on how long it takes for light to travel from the body to the Earth.

    This function corrects for *topocentric parallax*, meaning that it adjusts for the
    angular shift depending on where the observer is located on the Earth. This is most
    significant for the Moon, because it is so close to the Earth. However, parallax corection
    has a small effect on the apparent positions of other bodies.

    Correction for aberration is optional, using the `aberration` parameter.

    Parameters
    ----------
    body : Body
        The celestial body to be observed. Not allowed to be `Body.Earth`.
    time : Time
        The date and time at which the observation takes place.
    observer : Observer
        A location on or near the surface of the Earth.
    ofdate : bool
        Selects the date of the Earth's equator in which to express the equatorial coordinates.
        If `True`, returns coordinates using the equator and equinox of date.
        If `False`, returns coordinates converted to the J2000 system.
    aberration : bool
        If `True`, corrects for aberration of light based on the motion of the Earth
        with respect to the heliocentric origin.
        If `False`, does not correct for aberration.

    Returns
    -------
    #EquatorialCoordinates
        Equatorial coordinates in the specified frame of reference.
    """
    gc_observer = _geo_pos(time, observer)
    gc = GeoVector(body, time, aberration)
    j2000 = [
        gc.x - gc_observer[0],
        gc.y - gc_observer[1],
        gc.z - gc_observer[2]
    ]
    if not ofdate:
        return _vector2radec(j2000)
    temp = _precession(0, j2000, time.tt)
    datevect = _nutation(time, 0, temp)
    return _vector2radec(datevect)

@enum.unique
class Refraction(enum.IntEnum):
    """Selects if/how to correct for atmospheric refraction.

    Some functions allow enabling or disabling atmospheric refraction
    for the calculated apparent position of a celestial body
    as seen by an observer on the surface of the Earth.

    Values
    ------
    Airless:      No atmospheric refraction correction.
    Normal:       Recommended correction for standard atmospheric refraction.
    JplHorizons:  Used only for compatibility testing with JPL Horizons online tool.
    """
    Airless = 0
    Normal = 1
    JplHorizons = 2

class HorizontalCoordinates:
    """Coordinates of a celestial body as seen by a topocentric observer.

    Contains horizontal and equatorial coordinates as seen by an observer
    on or near the surface of the Earth (a topocentric observer).
    All coordinates are optionally corrected for atmospheric refraction.

    Attributes
    ----------
    azimuth : float
        The compass direction laterally around the observer's horizon,
        measured in degrees.
        North is 0 degrees, east is 90 degrees, south is 180 degrees, etc.
    altitude : float
        The angle in degrees above (positive) or below (negative) the observer's horizon.
    ra : float
        The right ascension in sidereal hours.
    dec : float
        The declination in degrees.
    """
    def __init__(self, azimuth, altitude, ra, dec):
        self.azimuth = azimuth
        self.altitude = altitude
        self.ra = ra
        self.dec = dec

def Horizon(time, observer, ra, dec, refraction):
    """Calculates the apparent location of a body relative to the local horizon of an observer on the Earth.

    Given a date and time, the geographic location of an observer on the Earth, and
    equatorial coordinates (right ascension and declination) of a celestial body,
    this function returns horizontal coordinates (azimuth and altitude angles) for the body
    relative to the horizon at the geographic location.

    The right ascension `ra` and declination `dec` passed in must be *equator of date*
    coordinates, based on the Earth's true equator at the date and time of the observation.
    Otherwise the resulting horizontal coordinates will be inaccurate.
    Equator of date coordinates can be obtained by calling #Equator, passing in
    `True` as its `ofdate` parameter. It is also recommended to enable
    aberration correction by passing in `True` for the `aberration` parameter.

    This function optionally corrects for atmospheric refraction.
    For most uses, it is recommended to pass `Refraction.Normal` in the `refraction` parameter to
    correct for optical lensing of the Earth's atmosphere that causes objects
    to appear somewhat higher above the horizon than they actually are.
    However, callers may choose to avoid this correction by passing in `Refraction.Airless`.
    If refraction correction is enabled, the azimuth, altitude, right ascension, and declination
    in the #HorizontalCoordinates object returned by this function will all be corrected for refraction.
    If refraction is disabled, none of these four coordinates will be corrected; in that case,
    the right ascension and declination in the returned object will be numerically identical
    to the respective `ra` and `dec` values passed in.

    Parameters
    ----------
    time : Time
        The date and time for which to find horizontal coordinates.
    observer : Observer
        The location of the observer for which to find horizontal coordinates.
    ra : float
        Right ascension in sidereal hours of the celestial object,
        referred to the mean equinox of date for the J2000 epoch.
    dec : float
        Declination in degrees of the celestial object,
        referred to the mean equator of date for the J2000 epoch.
        Positive values are north of the celestial equator
        and negative values are south of it.
    refraction : Refraction
        The option for selecting whether to correct for atmospheric lensing.
        If `Refraction.Normal`, a well-behaved refraction model is used.
        If `Refraction.None`, no refraction correct is performed.
        `Refraction.JplHorizons` is used only for compatibility testing
        with the JPL Horizons online tool.

    Returns
    -------
    #HorizontalCoordinates
        The horizontal coordinates (altitude and azimuth), along with
        equatorial coordinates (right ascension and declination), all
        optionally corrected for atmospheric refraction. See remarks above
        for more details.
    """
    if not (Refraction.Airless <= refraction <= Refraction.JplHorizons):
        raise Error('Invalid refraction type: ' + str(refraction))

    latrad = math.radians(observer.latitude)
    lonrad = math.radians(observer.longitude)
    decrad = math.radians(dec)
    rarad = math.radians(ra * 15.0)

    sinlat = math.sin(latrad)
    coslat = math.cos(latrad)
    sinlon = math.sin(lonrad)
    coslon = math.cos(lonrad)
    sindc = math.sin(decrad)
    cosdc = math.cos(decrad)
    sinra = math.sin(rarad)
    cosra = math.cos(rarad)

    uze = [coslat*coslon, coslat*sinlon, sinlat]
    une = [-sinlat*coslon, -sinlat*sinlon, coslat]
    uwe = [sinlon, -coslon, 0.0]

    angle = -15.0 * _sidereal_time(time)
    uz = _spin(angle, uze)
    un = _spin(angle, une)
    uw = _spin(angle, uwe)

    p = [cosdc*cosra, cosdc*sinra, sindc]

    pz = p[0]*uz[0] + p[1]*uz[1] + p[2]*uz[2]
    pn = p[0]*un[0] + p[1]*un[1] + p[2]*un[2]
    pw = p[0]*uw[0] + p[1]*uw[1] + p[2]*uw[2]

    proj = math.sqrt(pn*pn + pw*pw)
    az = 0.0
    if proj > 0.0:
        az = math.degrees(-math.atan2(pw, pn))
        if az < 0:
            az += 360
        if az >= 360:
            az -= 360
    zd = math.degrees(math.atan2(proj, pz))
    hor_ra = ra
    hor_dec = dec

    if refraction != Refraction.Airless:
        zd0 = zd
        refr = RefractionAngle(refraction, 90.0 - zd)
        zd -= refr
        if refr > 0.0 and zd > 3.0e-4:
            zdrad = math.radians(zd)
            sinzd = math.sin(zdrad)
            coszd = math.cos(zdrad)
            zd0rad = math.radians(zd0)
            sinzd0 = math.sin(zd0rad)
            coszd0 = math.cos(zd0rad)

            pr = [(((p[j] - coszd0 * uz[j]) / sinzd0)*sinzd + uz[j]*coszd) for j in range(3)]
            proj = math.sqrt(pr[0]*pr[0] + pr[1]*pr[1])
            if proj > 0:
                hor_ra = math.degrees(math.atan2(pr[1], pr[0])) / 15
                if hor_ra < 0:
                    hor_ra += 24
                if hor_ra >= 24:
                    hor_ra -= 24
            else:
                hor_ra = 0
            hor_dec = math.degrees(math.atan2(pr[2], proj))

    return HorizontalCoordinates(az, 90.0 - zd, hor_ra, hor_dec)

def RefractionAngle(refraction, altitude):
    """Calculates the amount of "lift" to an altitude angle caused by atmospheric refraction.

    Given an altitude angle and a refraction option, calculates
    the amount of "lift" caused by atmospheric refraction.
    This is the number of degrees higher in the sky an object appears
    due to lensing of the Earth's atmosphere.

    Parameters
    ----------
    refraction : Refraction
        The option for selecting whether to correct for atmospheric lensing.
        If `Refraction.Normal`, a well-behaved refraction model is used.
        If `Refraction.Airless`, no refraction correct is performed.
        `Refraction.JplHorizons` is used only for compatibility testing
        with the JPL Horizons online tool.
    altitude : float
        The number of degrees above (positive) or below (negative) the
        horizon an object is, before being corrected for refraction.

    Returns
    -------
    float
        The number of additional degrees of altitude an object appears
        to have, due to atmospheric refraction, depending on the
        option selected by the `refraction` parameter.
    """
    if altitude < -90.0 or altitude > +90.0:
        return 0.0      # No attempt to correct an invalid altitude

    if refraction == Refraction.Normal or refraction == Refraction.JplHorizons:
        # http://extras.springer.com/1999/978-1-4471-0555-8/chap4/horizons/horizons.pdf
        # JPL Horizons says it uses refraction algorithm from
        # Meeus "Astronomical Algorithms", 1991, p. 101-102.
        # I found the following Go implementation:
        # https://github.com/soniakeys/meeus/blob/master/v3/refraction/refract.go
        # This is a translation from the function "Saemundsson" there.
        # I found experimentally that JPL Horizons clamps the angle to 1 degree below the horizon.
        # This is important because the 'refr' formula below goes crazy near hd = -5.11.
        hd = max(altitude, -1.0)
        refr = (1.02 / math.tan(math.radians((hd+10.3/(hd+5.11))))) / 60.0

        if refraction == Refraction.Normal and altitude < -1.0:
            # In "normal" mode we gradually reduce refraction toward the nadir
            # so that we never get an altitude angle less than -90 degrees.
            # When horizon angle is -1 degrees, the factor is exactly 1.
            # As altitude approaches -90 (the nadir), the fraction approaches 0 linearly.
            refr *= (altitude + 90.0) / 89.0
    else:
        # No refraction, or the refraction option is invalid.
        refr = 0.0
    return refr

def InverseRefractionAngle(refraction, bent_altitude):
    """Calculates the inverse of an atmospheric refraction angle.

    Given an observed altitude angle that includes atmospheric refraction,
    calculate the negative angular correction to obtain the unrefracted
    altitude. This is useful for cases where observed horizontal
    coordinates are to be converted to another orientation system,
    but refraction first must be removed from the observed position.

    Parameters
    ----------
    refraction : Refraction
        `Refraction.Normal` - corrects for atmospheric refraction (recommended).
        `Refraction.Airless` - no correction is performed.
        `Refraction.JplHorizons` - For JPL Horizons compatibility testing only.
    bent_altitude : float
        The apparent altitude that includes atmospheric refraction.

    Returns
    -------
    float
        The angular adjustment in degrees, to be added to the
        altitude angle to correct for atmospheric lensing.
        This will be less than or equal to zero.
    """
    if bent_altitude < -90.0 or bent_altitude > +90.0:
        return 0.0      # No attempt to correct an invalid altitude
    # Find the pre-adjusted altitude whose refraction correction leads to 'altitude'.
    altitude = bent_altitude - RefractionAngle(refraction, bent_altitude)
    while True:
        # See how close we got. Keep iterating until the solution converges.
        diff = (altitude + RefractionAngle(refraction, altitude)) - bent_altitude
        if abs(diff) < 1.0e-14:
            return altitude - bent_altitude
        altitude -= diff

class EclipticCoordinates:
    """Ecliptic angular and Cartesian coordinates.

    Coordinates of a celestial body as seen from the center of the Sun (heliocentric),
    oriented with respect to the plane of the Earth's orbit around the Sun (the ecliptic).

    Attributes
    ----------
    ex : float
        Cartesian x-coordinate: in the direction of the equinox along the ecliptic plane.
    ey : float
        Cartesian y-coordinate: in the ecliptic plane 90 degrees prograde from the equinox.
    ez : float
        Cartesian z-coordinate: perpendicular to the ecliptic plane. Positive is north.
    elat : float
        Latitude in degrees north (positive) or south (negative) of the ecliptic plane.
    elon : float
        Longitude in degrees around the ecliptic plane prograde from the equinox.
    """
    def __init__(self, ex, ey, ez, elat, elon):
        self.ex = ex
        self.ey = ey
        self.ez = ez
        self.elat = elat
        self.elon = elon

def _RotateEquatorialToEcliptic(pos, obliq_radians):
    cos_ob = math.cos(obliq_radians)
    sin_ob = math.sin(obliq_radians)
    ex = +pos[0]
    ey = +pos[1]*cos_ob + pos[2]*sin_ob
    ez = -pos[1]*sin_ob + pos[2]*cos_ob
    xyproj = math.sqrt(ex*ex + ey*ey)
    if xyproj > 0.0:
        elon = math.degrees(math.atan2(ey, ex))
        if elon < 0.0:
            elon += 360.0
    else:
        elon = 0.0
    elat = math.degrees(math.atan2(ez, xyproj))
    return EclipticCoordinates(ex, ey, ez, elat, elon)

def SunPosition(time):
    """Calculates geocentric ecliptic coordinates for the Sun.

    This function calculates the position of the Sun as seen from the Earth.
    The returned value includes both Cartesian and spherical coordinates.
    The x-coordinate and longitude values in the returned object are based
    on the *true equinox of date*: one of two points in the sky where the instantaneous
    plane of the Earth's equator at the given date and time (the *equatorial plane*)
    intersects with the plane of the Earth's orbit around the Sun (the *ecliptic plane*).
    By convention, the apparent location of the Sun at the March equinox is chosen
    as the longitude origin and x-axis direction, instead of the one for September.

    `SunPosition` corrects for precession and nutation of the Earth's axis
    in order to obtain the exact equatorial plane at the given time.

    This function can be used for calculating changes of seasons: equinoxes and solstices.
    In fact, the function #Seasons does use this function for that purpose.

    Parameters
    ----------
    time : Time
        The date and time for which to calculate the Sun's position.

    Returns
    -------
    #EclipticCoordinates
        The ecliptic coordinates of the Sun using the Earth's true equator of date.
    """
    # Correct for light travel time from the Sun.
    # Otherwise season calculations (equinox, solstice) will all be early by about 8 minutes!
    adjusted_time = time.AddDays(-1.0 / _C_AUDAY)
    earth2000 = _CalcEarth(adjusted_time)
    sun2000 = [-earth2000.x, -earth2000.y, -earth2000.z]

    # Convert to equatorial Cartesian coordinates of date.
    stemp = _precession(0.0, sun2000, adjusted_time.tt)
    sun_ofdate = _nutation(adjusted_time, 0, stemp)

    # Convert equatorial coordinates to ecliptic coordinates.
    true_obliq = math.radians(adjusted_time._etilt().tobl)
    return _RotateEquatorialToEcliptic(sun_ofdate, true_obliq)

def Ecliptic(equ):
    """Converts J2000 equatorial Cartesian coordinates to J2000 ecliptic coordinates.

    Given coordinates relative to the Earth's equator at J2000 (the instant of noon UTC
    on 1 January 2000), this function converts those coordinates to J2000 ecliptic coordinates,
    which are relative to the plane of the Earth's orbit around the Sun.

    Parameters
    ----------
    equ : EquatorialCoordinates
        Equatorial coordinates in the J2000 frame of reference.

    Returns
    -------
    #EclipticCoordinates
        Ecliptic coordinates in the J2000 frame of reference.
    """
    # Based on NOVAS functions equ2ecl() and equ2ecl_vec().
    ob2000 = 0.40909260059599012   # mean obliquity of the J2000 ecliptic in radians
    return _RotateEquatorialToEcliptic([equ.x, equ.y, equ.z], ob2000)

def EclipticLongitude(body, time):
    """Calculates heliocentric ecliptic longitude of a body based on the J2000 equinox.

    This function calculates the angle around the plane of the Earth's orbit
    of a celestial body, as seen from the center of the Sun.
    The angle is measured prograde (in the direction of the Earth's orbit around the Sun)
    in degrees from the J2000 equinox. The ecliptic longitude is always in the range [0, 360).

    Parameters
    ----------
    body : Body
        A body other than the Sun.

    time : Time
        The date and time at which the body's ecliptic longitude is to be calculated.

    Returns
    -------
    `float`
        An angular value in degrees indicating the ecliptic longitude of the body.
    """
    if body == Body.Sun:
        raise InvalidBodyError()
    hv = HelioVector(body, time)
    eclip = Ecliptic(hv)
    return eclip.elon

def AngleFromSun(body, time):
    """Returns the angle between the given body and the Sun, as seen from the Earth.

    This function calculates the angular separation between the given body and the Sun,
    as seen from the center of the Earth. This angle is helpful for determining how
    easy it is to see the body away from the glare of the Sun.

    Parameters
    ----------
    body : Body
        The celestial body whose angle from the Sun is to be measured.
        Not allowed to be `Body.Earth`.
    time : Time
        The time at which the observation is made.

    Returns
    -------
    `float`
        A numeric value indicating the angle in degrees between the Sun
        and the specified body as seen from the center of the Earth.
    """
    if body == Body.Earth:
        raise EarthNotAllowedError()
    sv = GeoVector(Body.Sun, time, True)
    bv = GeoVector(body, time, True)
    return _AngleBetween(sv, bv)

def LongitudeFromSun(body, time):
    """Returns a body's ecliptic longitude with respect to the Sun, as seen from the Earth.

    This function can be used to determine where a planet appears around the ecliptic plane
    (the plane of the Earth's orbit around the Sun) as seen from the Earth,
    relative to the Sun's apparent position.

    The angle starts at 0 when the body and the Sun are at the same ecliptic longitude
    as seen from the Earth. The angle increases in the prograde direction
    (the direction that the planets orbit the Sun and the Moon orbits the Earth).

    When the angle is 180 degrees, it means the Sun and the body appear on opposite sides
    of the sky for an Earthly observer. When `body` is a planet whose orbit around the
    Sun is farther than the Earth's, 180 degrees indicates opposition. For the Moon,
    it indicates a full moon.

    The angle keeps increasing up to 360 degrees as the body's apparent prograde
    motion continues relative to the Sun. When the angle reaches 360 degrees, it starts
    over at 0 degrees.

    Values between 0 and 180 degrees indicate that the body is visible in the evening sky
    after sunset.  Values between 180 degrees and 360 degrees indicate that the body
    is visible in the morning sky before sunrise.

    Parameters
    ----------
    body : Body
        The celestial body for which to find longitude from the Sun.

    time : Time
        The date and time of the observation.

    Returns
    -------
    `float`
        An angle in degrees in the range [0, 360).
    """
    if body == Body.Earth:
        raise EarthNotAllowedError()
    sv = GeoVector(Body.Sun, time, True)
    se = Ecliptic(sv)
    bv = GeoVector(body, time, True)
    be = Ecliptic(bv)
    return _NormalizeLongitude(be.elon - se.elon)

class ElongationEvent:
    """Contains information about the visibility of a celestial body at a given date and time.

    See the #Elongation function for more detailed information about the members of this class.
    See also #SearchMaxElongation for how to search for maximum elongation events.

    Attributes
    ----------
    time : Time
        The date and time of the observation.
    visibility : Visibility
        Whether the body is best seen in the morning or the evening.
    elongation : float
        The angle in degrees between the body and the Sun, as seen from the Earth.
    ecliptic_separation : float
        The difference between the ecliptic longitudes of the body and the Sun, as seen from the Earth.
    """
    def __init__(self, time, visibility, elongation, ecliptic_separation):
        self.time = time
        self.visibility = visibility
        self.elongation = elongation
        self.ecliptic_separation = ecliptic_separation

class Visibility(enum.IntEnum):
    """Indicates whether a body (especially Mercury or Venus) is best seen in the morning or evening.

    Values
    ------
    Morning : The body is best visible in the morning, before sunrise.
    Evening : The body is best visible in the evening, after sunset.
    """
    Morning = 0
    Evening = 1

def Elongation(body, time):
    """Determines visibility of a celestial body relative to the Sun, as seen from the Earth.

    This function returns an #ElongationEvent object, which provides the following
    information about the given celestial body at the given time:

    - `visibility` is an enumerated type that specifies whether the body is more
      easily seen in the morning before sunrise, or in the evening after sunset.

    - `elongation` is the angle in degrees between two vectors: one from the center
      of the Earth to the center of the Sun, the other from the center of the Earth
      to the center of the specified body. This angle indicates how far away the body
      is from the glare of the Sun. The elongation angle is always in the range [0, 180].

    - `ecliptic_separation` is the absolute value of the difference between the body's
      ecliptic longitude and the Sun's ecliptic longitude, both as seen from the center
      of the Earth. This angle measures around the plane of the Earth's orbit, and ignores
      how far above or below that plane the body is.
      The ecliptic separation is measured in degrees and is always in the range [0, 180].

    Parameters
    ----------
    body : Body
        The celestial body whose visibility is to be calculated.

    time : Time
        The date and time of the observation.

    Returns
    -------
    #ElongationEvent
    """
    angle = LongitudeFromSun(body, time)
    if angle > 180.0:
        visibility = Visibility.Morning
        esep = 360.0 - angle
    else:
        visibility = Visibility.Evening
        esep = angle
    angle = AngleFromSun(body, time)
    return ElongationEvent(time, visibility, angle, esep)

def _rlon_offset(body, time, direction, targetRelLon):
    plon = EclipticLongitude(body, time)
    elon = EclipticLongitude(Body.Earth, time)
    diff = direction * (elon - plon)
    return _LongitudeOffset(diff - targetRelLon)

def SearchRelativeLongitude(body, targetRelLon, startTime):
    """Searches for when the Earth and another planet are separated by a certain ecliptic longitude.

    Searches for the time when the Earth and another planet are separated by a specified angle
    in ecliptic longitude, as seen from the Sun.

    A relative longitude is the angle between two bodies measured in the plane of the
    Earth's orbit (the ecliptic plane). The distance of the bodies above or below the ecliptic
    plane is ignored. If you imagine the shadow of the body cast onto the ecliptic plane,
    and the angle measured around that plane from one body to the other in the direction
    the planets orbit the Sun, you will get an angle somewhere between 0 and 360 degrees.
    This is the relative longitude.

    Given a planet other than the Earth in `body` and a time to start the search in `startTime`,
    this function searches for the next time that the relative longitude measured from the
    planet to the Earth is `targetRelLon`.

    Certain astronomical events are defined in terms of relative longitude between
    the Earth and another planet:

    - When the relative longitude is 0 degrees, it means both planets are in the same
      direction from the Sun. For planets that orbit closer to the Sun (Mercury and Venus),
      this is known as *inferior conjunction*, a time when the other planet becomes very
      difficult to see because of being lost in the Sun's glare.
      (The only exception is in the rare event of a transit, when we see the silhouette
      of the planet passing between the Earth and the Sun.)

    - When the relative longitude is 0 degrees and the other planet orbits farther from the Sun,
      this is known as *opposition*. Opposition is when the planet is closest to the Earth,
      and also when it is visible for most of the night, so it is considered the best time
      to observe the planet.

    - When the relative longitude is 180 degrees, it means the other planet is on the opposite
      side of the Sun from the Earth.  This is called *superior conjunction*.  Like inferior
      conjunction, the planet is very difficult to see from the Earth.
      Superior conjunction is possible for any planet other than the Earth.

    Parameters
    ----------
    body : Body
        A planet other than the Earth. If `body` is not a planet, or if it is `Body.Earth`, an error occurs.
    targetRelLon : float
        The desired relative longitude, expressed in degrees. Must be in the range [0, 360).
    startTime : Time
        The date and time at which to begin the search.

    Returns
    -------
    #Time
        The date and time of the relative longitude event.
    """
    if body == Body.Earth:
        raise EarthNotAllowedError()
    if body == Body.Moon or body == Body.Sun:
        raise InvalidBodyError()
    syn = _SynodicPeriod(body)
    direction = +1 if _IsSuperiorPlanet(body) else -1
    # Iterate until we converge on the desired event.
    # Calculate the error angle, which will be a negative number of degrees,
    # meaning we are "behind" the target relative longitude.
    error_angle = _rlon_offset(body, startTime, direction, targetRelLon)
    if error_angle > 0.0:
        error_angle -= 360.0    # force searching forward in time
    time = startTime
    iter = 0
    while iter < 100:
        # Estimate how many days in the future (positive) or past (negative)
        # we have to go to get closer to the target relative longitude.
        day_adjust = (-error_angle/360.0) * syn
        time = time.AddDays(day_adjust)
        if abs(day_adjust) * _SECONDS_PER_DAY < 1.0:
            return time
        prev_angle = error_angle
        error_angle = _rlon_offset(body, time, direction, targetRelLon)
        if abs(prev_angle) < 30.0 and prev_angle != error_angle:
            # Improve convergence for Mercury/Mars (eccentric orbits)
            # by adjusting the synodic period to more closely match the
            # variable speed of both planets in this part of their respective orbits.
            ratio = prev_angle / (prev_angle - error_angle)
            if 0.5 < ratio < 2.0:
                syn *= ratio
        iter += 1
    raise NoConvergeError()

def _neg_elong_slope(body, time):
    dt = 0.1
    t1 = time.AddDays(-dt/2.0)
    t2 = time.AddDays(+dt/2.0)
    e1 = AngleFromSun(body, t1)
    e2 = AngleFromSun(body, t2)
    return (e1 - e2)/dt

def SearchMaxElongation(body, startTime):
    """Finds a date and time when Mercury or Venus reaches its maximum angle from the Sun as seen from the Earth.

    Mercury and Venus are are often difficult to observe because they are closer to the Sun than the Earth is.
    Mercury especially is almost always impossible to see because it gets lost in the Sun's glare.
    The best opportunities for spotting Mercury, and the best opportunities for viewing Venus through
    a telescope without atmospheric interference, are when these planets reach maximum elongation.
    These are events where the planets reach the maximum angle from the Sun as seen from the Earth.

    This function solves for those times, reporting the next maximum elongation event's date and time,
    the elongation value itself, the relative longitude with the Sun, and whether the planet is best
    observed in the morning or evening. See #ElongationEvent for more details about the returned object.

    Parameters
    ----------
    body : Body
        Either `Body.Mercury` or `Body.Venus`. Any other value will result in an exception.
        To find the best viewing opportunities for planets farther from the Sun than the
        Earth is (Mars through Pluto), use #SearchRelativeLongitude to find the next opposition event.
    startTime : Time
        The date and time at which to begin the search. The maximum elongation event
        found will always be the first one that occurs after this date and time.

    Returns
    -------
    #ElongationEvent
    """
    if body == Body.Mercury:
        s1 = 50.0
        s2 = 85.0
    elif body == Body.Venus:
        s1 = 40.0
        s2 = 50.0
    else:
        raise InvalidBodyError()
    syn = _SynodicPeriod(body)
    iter = 1
    while iter <= 2:
        plon = EclipticLongitude(body, startTime)
        elon = EclipticLongitude(Body.Earth, startTime)
        rlon = _LongitudeOffset(plon - elon)    # clamp to (-180, +180]

        # The slope function is not well-behaved when rlon is near 0 degrees or 180 degrees
        # because there is a cusp there that causes a discontinuity in the derivative.
        # So we need to guard against searching near such times.
        if rlon >= -s1 and rlon < +s1:
            # Seek to the window [+s1, +s2].
            adjust_days = 0.0
            # Search forward for the time t1 when rel lon = +s1.
            rlon_lo = +s1
            # Search forward for the time t2 when rel lon = +s2.
            rlon_hi = +s2
        elif rlon > +s2 or rlon < -s2:
            # Seek to the next search window at [-s2, -s1].
            adjust_days = 0.0
            # Search forward for the time t1 when rel lon = -s2.
            rlon_lo = -s2
            # Search forward for the time t2 when rel lon = -s1.
            rlon_hi = -s1
        elif rlon >= 0.0:
            # rlon must be in the middle of the window [+s1, +s2].
            # Search BACKWARD for the time t1 when rel lon = +s1.
            adjust_days = -syn / 4.0
            rlon_lo = +s1
            rlon_hi = +s2
            # Search forward from t1 to find t2 such that rel lon = +s2.
        else:
            # rlon must be in the middle of the window [-s2, -s1].
            # Search BACKWARD for the time t1 when rel lon = -s2.
            adjust_days = -syn / 4.0
            rlon_lo = -s2
            # Search forward from t1 to find t2 such that rel lon = -s1.
            rlon_hi = -s1

        t_start = startTime.AddDays(adjust_days)
        t1 = SearchRelativeLongitude(body, rlon_lo, t_start)
        if t1 is None:
            return None

        t2 = SearchRelativeLongitude(body, rlon_hi, t1)
        if t2 is None:
            return None

        # Now we have a time range [t1,t2] that brackets a maximum elongation event.
        # Confirm the bracketing.
        m1 = _neg_elong_slope(body, t1)
        if m1 >= 0.0:
            raise InternalError()   # there is a bug in the bracketing algorithm!

        m2 = _neg_elong_slope(body, t2)
        if m2 <= 0.0:
            raise InternalError()   # there is a bug in the bracketing algorithm!

        # Use the generic search algorithm to home in on where the slope crosses from negative to positive.
        tx = Search(_neg_elong_slope, body, t1, t2, 10.0)
        if tx is None:
            return None

        if tx.tt >= startTime.tt:
            return Elongation(body, tx)

        # This event is in the past (earlier than startTime).
        # We need to search forward from t2 to find the next possible window.
        # We never need to search more than twice.
        startTime = t2.AddDays(1.0)
        iter += 1


def _sun_offset(targetLon, time):
    ecl = SunPosition(time)
    return _LongitudeOffset(ecl.elon - targetLon)

def SearchSunLongitude(targetLon, startTime, limitDays):
    """Searches for the time when the Sun reaches an apparent ecliptic longitude as seen from the Earth.

    This function finds the moment in time, if any exists in the given time window,
    that the center of the Sun reaches a specific ecliptic longitude as seen from the center of the Earth.

    This function can be used to determine equinoxes and solstices.
    However, it is usually more convenient and efficient to call #Seasons
    to calculate all equinoxes and solstices for a given calendar year.

    The function searches the window of time specified by `startTime` and `startTime+limitDays`.
    The search will return `None` if the Sun never reaches the longitude `targetLon` or
    if the window is so large that the longitude ranges more than 180 degrees within it.
    It is recommended to keep the window smaller than 10 days when possible.

    Parameters
    ----------

    targetLon : float
         The desired ecliptic longitude in degrees, relative to the true equinox of date.
         This may be any value in the range [0, 360), although certain values have
         conventional meanings:
         0 = March equinox, 90 = June solstice, 180 = September equinox, 270 = December solstice.
    startTime : Time
         The date and time for starting the search for the desired longitude event.
    limitDays : float
         The real-valued number of days, which when added to `startTime`, limits the
         range of time over which the search looks.
         It is recommended to keep this value between 1 and 10 days.
         See remarks above for more details.

    Returns
    -------
    #Time or `None`
    """
    t2 = startTime.AddDays(limitDays)
    return Search(_sun_offset, targetLon, startTime, t2, 1.0)

def MoonPhase(time):
    """Returns the Moon's phase as an angle from 0 to 360 degrees.

    This function determines the phase of the Moon using its apparent
    ecliptic longitude relative to the Sun, as seen from the center of the Earth.
    Certain values of the angle have conventional definitions:

    - 0 = new moon
    - 90 = first quarter
    - 180 = full moon
    - 270 = third quarter

    Parameters
    ----------
    time : Time
         The date and time of the observation.

    Returns
    -------
    `float`
    """
    return LongitudeFromSun(Body.Moon, time)

def _moon_offset(targetLon, time):
    angle = MoonPhase(time)
    return _LongitudeOffset(angle - targetLon)

def SearchMoonPhase(targetLon, startTime, limitDays):
    """Searches for the time that the Moon reaches a specified phase.

    Lunar phases are conventionally defined in terms of the Moon's geocentric ecliptic
    longitude with respect to the Sun's geocentric ecliptic longitude.
    When the Moon and the Sun have the same longitude, that is defined as a new moon.
    When their longitudes are 180 degrees apart, that is defined as a full moon.

    This function searches for any value of the lunar phase expressed as an
    angle in degrees in the range [0, 360).

    If you want to iterate through lunar quarters (new moon, first quarter, full moon, third quarter)
    it is much easier to call the functions #SearchMoonQuarter and #NextMoonQuarter.
    This function is useful for finding general phase angles outside those four quarters.

    Parameters
    ----------
    targetLon : float
         The difference in geocentric longitude between the Sun and Moon
         that specifies the lunar phase being sought. This can be any value
         in the range [0, 360).  Certain values have conventional names:
         0 = new moon, 90 = first quarter, 180 = full moon, 270 = third quarter.
    startTime : Time
         The beginning of the time window in which to search for the Moon reaching the specified phase.
    limitDays : float
         The number of days after `startTime` that limits the time window for the search.

    Returns
    -------
    #Time or `None`
    """
    # To avoid discontinuities in the _moon_offset function causing problems,
    # we need to approximate when that function will next return 0.
    # We probe it with the start time and take advantage of the fact
    # that every lunar phase repeats roughly every 29.5 days.
    # There is a surprising uncertainty in the quarter timing,
    # due to the eccentricity of the moon's orbit.
    # I have seen up to 0.826 days away from the simple prediction.
    # To be safe, we take the predicted time of the event and search
    # +/-0.9 days around it (a 1.8-day wide window).
    # But we must return None if the final result goes beyond limitDays after startTime.
    uncertainty = 0.9
    ya = _moon_offset(targetLon, startTime)
    if ya > 0.0:
        ya -= 360.0     # force searching forward in time, not backward
    est_dt = -(_MEAN_SYNODIC_MONTH * ya) / 360.0
    dt1 = est_dt - uncertainty
    if dt1 > limitDays:
        return None     # not possible for moon phase to occur within the specified window
    dt2 = min(limitDays, est_dt + uncertainty)
    t1 = startTime.AddDays(dt1)
    t2 = startTime.AddDays(dt2)
    return Search(_moon_offset, targetLon, t1, t2, 1.0)

class MoonQuarter:
    """A lunar quarter event along with its date and time.

    An object of this type represents one of the four major
    lunar phases that appear on calendars:
    new moon, first quarter, full moon, or third quarter.
    Along with the `quarter` attribute that specifies the
    type of quarter, it contains a `time` field that indicates
    when the lunar quarter event happens.

    Attributes
    ----------
    quarter : int
        0=new moon, 1=first quarter, 2=full moon, 3=third quarter.
    time : Time
        The date and time of the lunar quarter.
    """
    def __init__(self, quarter, time):
        self.quarter = quarter
        self.time = time

def SearchMoonQuarter(startTime):
    """Finds the first lunar quarter after the specified date and time.

    A lunar quarter is one of the following four lunar phase events:
    new moon, first quarter, full moon, third quarter.
    This function finds the lunar quarter that happens soonest
    after the specified date and time.

    To continue iterating through consecutive lunar quarters, call this function once,
    followed by calls to #NextMoonQuarter as many times as desired.

    Parameters
    ----------
    startTime : Time
        The date and time at which to start the search.

    Returns
    -------
    #MoonQuarter
    """
    angle = MoonPhase(startTime)
    quarter = int(1 + math.floor(angle / 90.0)) % 4
    time = SearchMoonPhase(90.0 * quarter, startTime, 10.0)
    if time is None:
        # The search should never fail. We should always find another lunar quarter.
        raise InternalError()
    return MoonQuarter(quarter, time)

def NextMoonQuarter(mq):
    """Continues searching for lunar quarters from a previous search.

    After calling #Astronomy_SearchMoonQuarter, this function can be called
    one or more times to continue finding consecutive lunar quarters.
    This function finds the next consecutive moon quarter event after
    the one passed in as the parameter `mq`.

    Parameters
    ----------
    mq : MoonQuarter
        A value returned by a prior call to #SearchMoonQuarter or #NextMoonQuarter.

    Returns
    -------
    #MoonQuarter
    """
    # Skip 6 days past the previous found moon quarter to find the next one.
    # This is less than the minimum possible increment.
    # So far I have seen the interval well contained by the range (6.5, 8.3) days.
    time = mq.time.AddDays(6.0)
    next_mq = SearchMoonQuarter(time)
    # Verify that we found the expected moon quarter.
    if next_mq.quarter != (1 + mq.quarter) % 4:
        raise InternalError()
    return next_mq


class IlluminationInfo:
    """Information about the brightness and illuminated shape of a celestial body.

    Returned by functions #Illumination and #SearchPeakMagnitude
    to report the visual magnitude and illuminated fraction of a celestial
    body at a given date and time.

    Attributes
    ----------
    time : Time
        The date and time of the observation.
    mag : float
        The visual magnitude of the body. Smaller values are brighter.
    phase_angle : float
        The angle in degrees between the Sun and the Earth, as seen from the body.
        Indicates the body's phase as seen from the Earth.
    phase_fraction : float
        A value in the range [0.0, 1.0] indicating what fraction of the
        body's apparent disc is illuminated, as seen from the Earth.
    helio_dist : float
        The distance between the Sun and the body at the observation time, in AU.
    ring_tilt : float
        For Saturn, the tilt angle in degrees of its rings as seen from Earth.
        When the `ring_tilt` is very close to 0, it means the rings are edge-on
        as seen from observers on the Earth, and are thus very difficult to see.
        For bodies other than Saturn, `ring_tilt` is `None`.
    """
    def __init__(self, time, mag, phase, helio_dist, geo_dist, gc, hc, ring_tilt):
        self.time = time
        self.mag = mag
        self.phase_angle = phase
        self.phase_fraction = (1.0 + math.cos(math.radians(phase))) / 2.0
        self.helio_dist = helio_dist
        self.geo_dist = geo_dist
        self.gc = gc
        self.hc = hc
        self.ring_tilt = ring_tilt

def _MoonMagnitude(phase, helio_dist, geo_dist):
    # https://astronomy.stackexchange.com/questions/10246/is-there-a-simple-analytical-formula-for-the-lunar-phase-brightness-curve
    rad = math.radians(phase)
    mag = -12.717 + 1.49*abs(rad) + 0.0431*(rad**4)
    moon_mean_distance_au = 385000.6 / _KM_PER_AU
    geo_au = geo_dist / moon_mean_distance_au
    mag += 5.0 * math.log10(helio_dist * geo_au)
    return mag

def _SaturnMagnitude(phase, helio_dist, geo_dist, gc, time):
    # Based on formulas by Paul Schlyter found here:
    # http://www.stjarnhimlen.se/comp/ppcomp.html#15

    # We must handle Saturn's rings as a major component of its visual magnitude.
    # Find geocentric ecliptic coordinates of Saturn.
    eclip = Ecliptic(gc)

    ir = math.radians(28.06)   # tilt of Saturn's rings to the ecliptic, in radians
    Nr = math.radians(169.51 + (3.82e-5 * time.tt))    # ascending node of Saturn's rings, in radians

    # Find tilt of Saturn's rings, as seen from Earth.
    lat = math.radians(eclip.elat)
    lon = math.radians(eclip.elon)
    tilt = math.asin(math.sin(lat)*math.cos(ir) - math.cos(lat)*math.sin(ir)*math.sin(lon-Nr))
    sin_tilt = math.sin(abs(tilt))

    mag = -9.0 + 0.044*phase
    mag += sin_tilt*(-2.6 + 1.2*sin_tilt)
    mag += 5.0 * math.log10(helio_dist * geo_dist)
    ring_tilt = math.degrees(tilt)
    return (mag, ring_tilt)

def _VisualMagnitude(body, phase, helio_dist, geo_dist):
    # For Mercury and Venus, see:  https://iopscience.iop.org/article/10.1086/430212
    c0 = c1 = c2 = c3 = 0
    if body == Body.Mercury:
        c0 = -0.60; c1 = +4.98; c2 = -4.88; c3 = +3.02
    elif body == Body.Venus:
        if phase < 163.6:
            c0 = -4.47; c1 = +1.03; c2 = +0.57; c3 = +0.13
        else:
            c0 = +0.98; c1 = -1.02
    elif body == Body.Mars:
        c0 = -1.52; c1 = +1.60
    elif body == Body.Jupiter:
        c0 = -9.40; c1 = +0.50
    elif body == Body.Uranus:
        c0 = -7.19; c1 = +0.25
    elif body == Body.Neptune:
        c0 = -6.87
    elif body == Body.Pluto:
        c0 = -1.00; c1 = +4.00
    else:
        raise InvalidBodyError()

    x = phase / 100.0
    mag = c0 + x*(c1 + x*(c2 + x*c3))
    mag += 5.0 * math.log10(helio_dist * geo_dist)
    return mag

def Illumination(body, time):
    """Finds visual magnitude, phase angle, and other illumination information about a celestial body.

    This function calculates information about how bright a celestial body appears from the Earth,
    reported as visual magnitude, which is a smaller (or even negative) number for brighter objects,
    and a larger number for dimmer objects.

    For bodies other than the Sun, it reports a phase angle, which is the angle in degrees between
    the Sun and the Earth, as seen from the center of the body. Phase angle indicates what fraction
    of the body appears illuminated as seen from the Earth. For example, when the phase angle is
    near zero, it means the body appears "full" as seen from the Earth.  A phase angle approaching
    180 degrees means the body appears as a thin crescent as seen from the Earth.  A phase angle
    of 90 degrees means the body appears "half full".
    For the Sun, the phase angle is always reported as 0; the Sun emits light rather than reflecting it,
    so it doesn't have a phase angle.

    When the body is Saturn, the returned object contains a field `ring_tilt` that holds
    the tilt angle in degrees of Saturn's rings as seen from the Earth. A value of 0 means
    the rings appear edge-on, and are thus nearly invisible from the Earth. The `ring_tilt` holds
    0 for all bodies other than Saturn.

    Parameters
    ----------
    body : Body
        The Sun, Moon, or any planet other than the Earth.
    time : Time
        The date and time of the observation.

    Returns
    -------
    #IlluminationInfo
    """
    if body == Body.Earth:
        raise EarthNotAllowedError()
    earth = _CalcEarth(time)
    if body == Body.Sun:
        gc = Vector(-earth.x, -earth.y, -earth.z, time)
        hc = Vector(0.0, 0.0, 0.0, time)
        phase = 0.0     # placeholder value; the Sun does not have a phase angle.
    else:
        if body == Body.Moon:
            # For extra numeric precision, use geocentric moon formula directly.
            gc = GeoMoon(time)
            hc = Vector(earth.x + gc.x, earth.y + gc.y, earth.z + gc.z, time)
        else:
            # For planets, heliocentric vector is most direct to calculate.
            hc = HelioVector(body, time)
            gc = Vector(hc.x - earth.x, hc.y - earth.y, hc.z - earth.z, time)
        phase = _AngleBetween(gc, hc)

    geo_dist = gc.Length()      # distance from body to center of Earth
    helio_dist = hc.Length()    # distance from body to center of Sun
    ring_tilt = None            # only reported for Saturn
    if body == Body.Sun:
        mag = -0.17 + 5.0*math.log10(geo_dist / _AU_PER_PARSEC)
    elif body == Body.Moon:
        mag = _MoonMagnitude(phase, helio_dist, geo_dist)
    elif body == Body.Saturn:
        mag, ring_tilt = _SaturnMagnitude(phase, helio_dist, geo_dist, gc, time)
    else:
        mag = _VisualMagnitude(body, phase, helio_dist, geo_dist)
    return IlluminationInfo(time, mag, phase, helio_dist, geo_dist, gc, hc, ring_tilt)

def _mag_slope(body, time):
    # The Search() function finds a transition from negative to positive values.
    # The derivative of magnitude y with respect to time t (dy/dt)
    # is negative as an object gets brighter, because the magnitude numbers
    # get smaller. At peak magnitude dy/dt = 0, then as the object gets dimmer,
    # dy/dt > 0.
    dt = 0.01
    t1 = time.AddDays(-dt/2)
    t2 = time.AddDays(+dt/2)
    y1 = Illumination(body, t1)
    y2 = Illumination(body, t2)
    return (y2.mag - y1.mag) / dt

def SearchPeakMagnitude(body, startTime):
    """Searches for the date and time Venus will next appear brightest as seen from the Earth.

    This function searches for the date and time Venus appears brightest as seen from the Earth.
    Currently only Venus is supported for the `body` parameter, though this could change in the future.
    Mercury's peak magnitude occurs at superior conjunction, when it is virtually impossible to see
    from the Earth, so peak magnitude events have little practical value for that planet.
    Planets other than Venus and Mercury reach peak magnitude at opposition, which can
    be found using #SearchRelativeLongitude.
    The Moon reaches peak magnitude at full moon, which can be found using
    #SearchMoonQuarter or #SearchMoonPhase.
    The Sun reaches peak magnitude at perihelion, which occurs each year in January.
    However, the difference is minor and has little practical value.

    Parameters
    ----------
    body : Body
        Currently only `Body.Venus` is allowed. Any other value results in an exception.
        See remarks above for more details.
    startTime : Time
        The date and time to start searching for the next peak magnitude event.

    Returns
    -------
    #IlluminationInfo
    """
    # s1 and s2 are relative longitudes within which peak magnitude of Venus can occur.
    s1 = 10.0
    s2 = 30.0
    if body != Body.Venus:
        raise InvalidBodyError()

    iter = 1
    while iter <= 2:
        # Find current heliocentric relative longitude between the
        # inferior planet and the Earth.
        plon = EclipticLongitude(body, startTime)
        elon = EclipticLongitude(Body.Earth, startTime)
        rlon = _LongitudeOffset(plon - elon)
        # The slope function is not well-behaved when rlon is near 0 degrees or 180 degrees
        # because there is a cusp there that causes a discontinuity in the derivative.
        # So we need to guard against searching near such times.
        if -s1 <= rlon < +s1:
            # Seek to the window [+s1, +s2].
            adjust_days = 0.0
            # Search forward for the time t1 when rel lon = +s1.
            rlon_lo = +s1
            # Search forward for the time t2 when rel lon = +s2.
            rlon_hi = +s2
        elif rlon >= +s2 or rlon < -s2:
            # Seek to the next search window at [-s2, -s1].
            adjust_days = 0.0
            # Search forward for the time t1 when rel lon = -s2.
            rlon_lo = -s2
            # Search forward for the time t2 when rel lon = -s1.
            rlon_hi = -s1
        elif rlon >= 0:
            # rlon must be in the middle of the window [+s1, +s2].
            # Search BACKWARD for the time t1 when rel lon = +s1.
            syn = _SynodicPeriod(body)
            adjust_days = -syn / 4
            rlon_lo = +s1
            # Search forward from t1 to find t2 such that rel lon = +s2.
            rlon_hi = +s2
        else:
            # rlon must be in the middle of the window [-s2, -s1].
            # Search BACKWARD for the time t1 when rel lon = -s2.
            syn = _SynodicPeriod(body)
            adjust_days = -syn / 4
            rlon_lo = -s2
            # Search forward from t1 to find t2 such that rel lon = -s1.
            rlon_hi = -s1

        t_start = startTime.AddDays(adjust_days)
        t1 = SearchRelativeLongitude(body, rlon_lo, t_start)
        t2 = SearchRelativeLongitude(body, rlon_hi, t1)

        # Now we have a time range [t1,t2] that brackets a maximum magnitude event.
        # Confirm the bracketing.
        m1 = _mag_slope(body, t1)
        if m1 >= 0.0:
            raise InternalError()

        m2 = _mag_slope(body, t2)
        if m2 <= 0.0:
            raise InternalError()

        # Use the generic search algorithm to home in on where the slope crosses from negative to positive.
        tx = Search(_mag_slope, body, t1, t2, 10.0)
        if tx is None:
            # The search should have found the ascending root in the interval [t1, t2].
            raise InternalError()

        if tx.tt >= startTime.tt:
            return Illumination(body, tx)

        # This event is in the past (earlier than startTime).
        # We need to search forward from t2 to find the next possible window.
        # We never need to search more than twice.
        startTime = t2.AddDays(1.0)
        iter += 1

    # We should have found the peak magnitude in at most 2 iterations.
    raise InternalError()

class HourAngleEvent:
    """Information about a celestial body crossing a specific hour angle.

    Returned by the function #Astronomy_SearchHourAngle to report information about
    a celestial body crossing a certain hour angle as seen by a specified topocentric observer.

    Attributes
    ----------
    time : Time
        The date and time when the body crosses the specified hour angle.
    hor : HorizontalCoordinates
        Apparent coordinates of the body at the time it crosses the specified hour angle.
    """
    def __init__(self, time, hor):
        self.time = time
        self.hor = hor

def SearchHourAngle(body, observer, hourAngle, startTime):
    """Searches for the time when a celestial body reaches a specified hour angle as seen by an observer on the Earth.

    The *hour angle* of a celestial body indicates its position in the sky with respect
    to the Earth's rotation. The hour angle depends on the location of the observer on the Earth.
    The hour angle is 0 when the body reaches its highest angle above the horizon in a given day.
    The hour angle increases by 1 unit for every sidereal hour that passes after that point, up
    to 24 sidereal hours when it reaches the highest point again. So the hour angle indicates
    the number of hours that have passed since the most recent time that the body has culminated,
    or reached its highest point.

    This function searches for the next time a celestial body reaches the given hour angle
    after the date and time specified by `startTime`.
    To find when a body culminates, pass 0 for `hourAngle`.
    To find when a body reaches its lowest point in the sky, pass 12 for `hourAngle`.

    Note that, especially close to the Earth's poles, a body as seen on a given day
    may always be above the horizon or always below the horizon, so the caller cannot
    assume that a culminating object is visible nor that an object is below the horizon
    at its minimum altitude.

    On success, the function reports the date and time, along with the horizontal coordinates
    of the body at that time, as seen by the given observer.

    Parameters
    ----------
    body : Body
         The celestial body, which can the Sun, the Moon, or any planet other than the Earth.
    observer : Observer
         Indicates a location on or near the surface of the Earth where the observer is located.
    hourAngle : float
         An hour angle value in the range [0.0, 24.0) indicating the number of sidereal hours after the
         body's most recent culmination.
    startTime : Time
         The date and time at which to start the search.

    Returns
    -------
    #HourAngleEvent
    """
    if body == Body.Earth:
        raise EarthNotAllowedError()

    if hourAngle < 0.0 or hourAngle >= 24.0:
        raise Error('Invalid hour angle.')

    iter = 0
    time = startTime
    while True:
        iter += 1
        # Calculate Greenwich Apparent Sidereal Time (GAST) at the given time.
        gast = _sidereal_time(time)
        ofdate = Equator(body, time, observer, True, True)

        # Calculate the adjustment needed in sidereal time to bring
        # the hour angle to the desired value.
        delta_sidereal_hours = math.fmod(((hourAngle + ofdate.ra - observer.longitude/15) - gast), 24.0)
        if iter == 1:
            # On the first iteration, always search forward in time.
            if delta_sidereal_hours < 0.0:
                delta_sidereal_hours += 24.0
        else:
            # On subsequent iterations, we make the smallest possible adjustment,
            # either forward or backward in time.
            if delta_sidereal_hours < -12.0:
                delta_sidereal_hours += 24.0
            elif delta_sidereal_hours > +12.0:
                delta_sidereal_hours -= 24.0

        # If the error is tolerable (less than 0.1 seconds), stop searching.
        if abs(delta_sidereal_hours) * 3600.0 < 0.1:
            hor = Horizon(time, observer, ofdate.ra, ofdate.dec, Refraction.Normal)
            return HourAngleEvent(time, hor)

        # We need to loop another time to get more accuracy.
        # Update the terrestrial time (in solar days) adjusting by sidereal time.
        delta_days = (delta_sidereal_hours / 24.0) * _SOLAR_DAYS_PER_SIDEREAL_DAY
        time = time.AddDays(delta_days)

@enum.unique
class Direction(enum.IntEnum):
    """Indicates whether a body is rising above or setting below the horizon.

    Specifies the direction of a rising or setting event for a body.
    For example, `Direction.Rise` is used to find sunrise times,
    and `Direction.Set` is used to find sunset times.

    Values
    ------
    Rise:   First appearance of a body as it rises above the horizon.
    Set:    Last appearance of a body as it sinks below the horizon.
    """
    Rise = +1
    Set  = -1

class _peak_altitude_context:
    def __init__(self, body, direction, observer, body_radius_au):
        self.body = body
        self.direction = direction
        self.observer = observer
        self.body_radius_au = body_radius_au

def _peak_altitude(context, time):
    # Return the angular altitude above or below the horizon
    # of the highest part (the peak) of the given object.
    # This is defined as the apparent altitude of the center of the body plus
    # the body's angular radius.
    # The 'direction' parameter controls whether the angle is measured
    # positive above the horizon or positive below the horizon,
    # depending on whether the caller wants rise times or set times, respectively.

    ofdate = Equator(context.body, time, context.observer, True, True)

    # We calculate altitude without refraction, then add fixed refraction near the horizon.
    # This gives us the time of rise/set without the extra work.
    hor = Horizon(time, context.observer, ofdate.ra, ofdate.dec, Refraction.Airless)
    alt = hor.altitude + math.degrees(context.body_radius_au / ofdate.dist)
    return context.direction * (alt + _REFRACTION_NEAR_HORIZON)

def SearchRiseSet(body, observer, direction, startTime, limitDays):
    """Searches for the next time a celestial body rises or sets as seen by an observer on the Earth.

    This function finds the next rise or set time of the Sun, Moon, or planet other than the Earth.
    Rise time is when the body first starts to be visible above the horizon.
    For example, sunrise is the moment that the top of the Sun first appears to peek above the horizon.
    Set time is the moment when the body appears to vanish below the horizon.

    This function corrects for typical atmospheric refraction, which causes celestial
    bodies to appear higher above the horizon than they would if the Earth had no atmosphere.
    It also adjusts for the apparent angular radius of the observed body (significant only for the Sun and Moon).

    Note that rise or set may not occur in every 24 hour period.
    For example, near the Earth's poles, there are long periods of time where
    the Sun stays below the horizon, never rising.
    Also, it is possible for the Moon to rise just before midnight but not set during the subsequent 24-hour day.
    This is because the Moon sets nearly an hour later each day due to orbiting the Earth a
    significant amount during each rotation of the Earth.
    Therefore callers must not assume that the function will always succeed.

    Parameters
    ----------
    body : Body
        The Sun, Moon, or any planet other than the Earth.
    observer : Observer
        The location where observation takes place.
    direction : Direction
        Either `Direction.Rise` to find a rise time or `Direction.Set` to find a set time.
    startTime : Time
        The date and time at which to start the search.
    limitDays : float
        Limits how many days to search for a rise or set time.
        To limit a rise or set time to the same day, you can use a value of 1 day.
        In cases where you want to find the next rise or set time no matter how far
        in the future (for example, for an observer near the south pole), you can pass
        in a larger value like 365.

    Returns
    -------
    #Time or `None`
        If the rise or set time is found within the specified time window,
        this function returns that time. Otherwise, it returns `None`.
    """
    if body == Body.Earth:
        raise EarthNotAllowedError()
    elif body == Body.Sun:
        body_radius = _SUN_RADIUS_AU
    elif body == Body.Moon:
        body_radius = _MOON_RADIUS_AU
    else:
        body_radius = 0.0

    if direction == Direction.Rise:
        ha_before = 12.0    # minimum altitude (bottom) happens BEFORE the body rises.
        ha_after  =  0.0    # maximum altitude (culmination) happens AFTER the body rises.
    elif direction == Direction.Set:
        ha_before =  0.0    # culmination happens BEFORE the body sets.
        ha_after  = 12.0    # bottom happens AFTER the body sets.
    else:
        raise Error('Invalid value for direction parameter')

    context = _peak_altitude_context(body, direction, observer, body_radius)

    # See if the body is currently above/below the horizon.
    # If we are looking for next rise time and the body is below the horizon,
    # we use the current time as the lower time bound and the next culmination
    # as the upper bound.
    # If the body is above the horizon, we search for the next bottom and use it
    # as the lower bound and the next culmination after that bottom as the upper bound.
    # The same logic applies for finding set times, only we swap the hour angles.
    time_start = startTime
    alt_before = _peak_altitude(context, time_start)
    if alt_before > 0.0:
        # We are past the sought event, so we have to wait for the next "before" event (culm/bottom).
        evt_before = SearchHourAngle(body, observer, ha_before, time_start)
        time_before = evt_before.time
        alt_before = _peak_altitude(context, time_before)
    else:
        # We are before or at the sought ebvent, so we find the next "after" event (bottom/culm),
        # and use the current time as the "before" event.
        time_before = time_start

    evt_after = SearchHourAngle(body, observer, ha_after, time_before)
    alt_after = _peak_altitude(context, evt_after.time)

    while True:
        if alt_before <= 0.0 and alt_after > 0.0:
            # Search between the "before time" and the "after time" for the desired event.
            event_time = Search(_peak_altitude, context, time_before, evt_after.time, 1.0)
            if event_time is not None:
                return event_time
        # We didn't find the desired event, so use the "after" time to find the next "before" event.
        evt_before = SearchHourAngle(body, observer, ha_before, evt_after.time)
        evt_after = SearchHourAngle(body, observer, ha_after, evt_before.time)
        if evt_before.time.ut >= time_start.ut + limitDays:
            return None
        time_before = evt_before.time
        alt_before = _peak_altitude(context, evt_before.time)
        alt_after = _peak_altitude(context, evt_after.time)

class SeasonInfo:
    """The dates and times of changes of season for a given calendar year.

    Call #Seasons to calculate this data structure for a given year.

    Attributes
    ----------
    mar_equinox : Time
        The date and time of the March equinox for the specified year.
    jun_solstice : Time
        The date and time of the June solstice for the specified year.
    sep_equinox : Time
        The date and time of the September equinox for the specified year.
    dec_solstice : Time
        The date and time of the December solstice for the specified year.
    """
    def __init__(self, mar_equinox, jun_solstice, sep_equinox, dec_solstice):
        self.mar_equinox = mar_equinox
        self.jun_solstice = jun_solstice
        self.sep_equinox = sep_equinox
        self.dec_solstice = dec_solstice

def _FindSeasonChange(targetLon, year, month, day):
    startTime = Time.Make(year, month, day, 0, 0, 0)
    time = SearchSunLongitude(targetLon, startTime, 4.0)
    if time is None:
        # We should always be able to find a season change.
        raise InternalError()
    return time

def Seasons(year):
    """Finds both equinoxes and both solstices for a given calendar year.

    The changes of seasons are defined by solstices and equinoxes.
    Given a calendar year number, this function calculates the
    March and September equinoxes and the June and December solstices.

    The equinoxes are the moments twice each year when the plane of the
    Earth's equator passes through the center of the Sun. In other words,
    the Sun's declination is zero at both equinoxes.
    The March equinox defines the beginning of spring in the northern hemisphere
    and the beginning of autumn in the southern hemisphere.
    The September equinox defines the beginning of autumn in the northern hemisphere
    and the beginning of spring in the southern hemisphere.

    The solstices are the moments twice each year when one of the Earth's poles
    is most tilted toward the Sun. More precisely, the Sun's declination reaches
    its minimum value at the December solstice, which defines the beginning of
    winter in the northern hemisphere and the beginning of summer in the southern
    hemisphere. The Sun's declination reaches its maximum value at the June solstice,
    which defines the beginning of summer in the northern hemisphere and the beginning
    of winter in the southern hemisphere.

    Parameters
    ----------
    year : int
        The calendar year number for which to calculate equinoxes and solstices.
        The value may be any integer, but only the years 1800 through 2100 have
        been validated for accuracy: unit testing against data from the
        United States Naval Observatory confirms that all equinoxes and solstices
        for that range of years are within 2 minutes of the correct time.

    Returns
    -------
    #SeasonInfo
    """
    mar_equinox = _FindSeasonChange(0, year, 3, 19)
    jun_solstice = _FindSeasonChange(90, year, 6, 19)
    sep_equinox = _FindSeasonChange(180, year, 9, 21)
    dec_solstice = _FindSeasonChange(270, year, 12, 20)
    return SeasonInfo(mar_equinox, jun_solstice, sep_equinox, dec_solstice)

def _MoonDistance(time):
    return _CalcMoon(time).distance_au

def _distance_slope(direction, time):
    dt = 0.001
    t1 = time.AddDays(-dt/2.0)
    t2 = time.AddDays(+dt/2.0)
    dist1 = _MoonDistance(t1)
    dist2 = _MoonDistance(t2)
    return direction * (dist2 - dist1) / dt

@enum.unique
class ApsisKind(enum.IntEnum):
    """Represents whether a satellite is at a closest or farthest point in its orbit.

    An apsis is a point in a satellite's orbit that is closest to,
    or farthest from, the body it orbits (its primary).
    `ApsisKind` is an enumerated type that indicates which of these
    two cases applies to a particular apsis event.

    Values
    ------
    Pericenter: The satellite is at its closest point to its primary.
    Apocenter: The satellite is at its farthest point from its primary.
    Invalid: A placeholder for an undefined, unknown, or invalid apsis.
    """
    Pericenter = 0
    Apocenter  = 1
    Invalid    = 2

class Apsis:
    """An event where a satellite is closest to or farthest from the body it orbits.

    For the Moon orbiting the Earth, or a planet orbiting the Sun, an *apsis* is an
    event where the orbiting body reaches its closest or farthest point from the primary body.
    The closest approach is called *pericenter* and the farthest point is *apocenter*.

    More specific terminology is common for particular orbiting bodies.
    The Moon's closest approach to the Earth is called *perigee* and its furthest
    point is called *apogee*. The closest approach of a planet to the Sun is called
    *perihelion* and the furthest point is called *aphelion*.

    This data structure is returned by #SearchLunarApsis and #NextLunarApsis
    to iterate through consecutive alternating perigees and apogees.

    Attributes
    ----------
    time : Time
        The date and time of the apsis.
    kind : ApsisKind
        Whether this is a pericenter or apocenter event.
    dist_au : float
        The distance between the centers of the bodies in astronomical units.
    dist_km : float
        The distance between the centers of the bodies in kilometers.
    """
    def __init__(self, time, kind, dist_au):
        self.time = time
        self.kind = kind
        self.dist_au = dist_au
        self.dist_km = dist_au * _KM_PER_AU

def SearchLunarApsis(startTime):
    """Finds the time of the first lunar apogee or perigee after the given time.

    Given a date and time to start the search in `startTime`, this function finds
    the next date and time that the center of the Moon reaches the closest or
    farthest point in its orbit with respect to the center of the Earth, whichever
    comes first after `startTime`.  The return value (of type #Apsis) also
    contains an indicator of whether the event is apogee or perigee.

    The closest point is called *perigee* and the farthest point is called *apogee*.
    The word *apsis* refers to either event.

    To iterate through consecutive alternating perigee and apogee events,
    call #SearchLunarApsis once, then use the return value to call #NextLunarApsis.
    After that, keep feeding the previous return value from `NextLunarApsis` into
    another call of `NextLunarApsis` as many times as desired.

    Parameters
    ----------
    startTime : Time
        The date and time at which to start searching for the next perigee or apogee.

    Returns
    -------
    #Apsis
    """
    increment = 5.0     # number of days to skip on each iteration
    t1 = startTime
    m1 = _distance_slope(+1, t1)
    iter = 0
    while iter * increment < 2.0 * _MEAN_SYNODIC_MONTH:
        t2 = t1.AddDays(increment)
        m2 = _distance_slope(+1, t2)
        if m1 * m2 <= 0.0:
            # There is a change of slope polarity within the time range [t1, t2].
            # Therefore this time range contains an apsis.
            # Figure out whether it is perigee or apogee.
            if m1 < 0.0 or m2 > 0.0:
                # We found a minimum-distance event: perigee.
                # Search the time range for the time when the slope goes from negative to positive.
                apsis_time = Search(_distance_slope, +1, t1, t2, 1.0)
                kind = ApsisKind.Pericenter
            elif m1 > 0.0 or m2 < 0.0:
                # We found a maximum-distance event: apogee.
                # Search the time range for the time when the slope goes from positive to negative.
                apsis_time = Search(_distance_slope, -1, t1, t2, 1.0)
                kind = ApsisKind.Apocenter
            else:
                # This should never happen. It should not be possible for both slopes to be zero.
                raise InternalError()

            if apsis_time is None:
                # We should always be able to find a lunar apsis!
                raise InternalError()

            dist = _MoonDistance(apsis_time)
            return Apsis(apsis_time, kind, dist)

        # We have not yet found a slope polarity change. Keep searching.
        t1 = t2
        m1 = m2
        iter += 1

    # It should not be possible to fail to find an apsis within 2 synodic months.
    raise InternalError()


def NextLunarApsis(apsis):
    """Finds the next lunar perigee or apogee in a series.

    This function requires an #Apsis value obtained from a call to
    #SearchLunarApsis or `NextLunarApsis`.
    Given an apogee event, this function finds the next perigee event,
    and vice versa.

    See #SearchLunarApsis for more details.

    Parameters
    ----------
    apsis : Apsis

    Returns
    -------
    #Apsis
    """
    skip = 11.0     # number of days to skip to start looking for next apsis event
    time = apsis.time.AddDays(skip)
    next = SearchLunarApsis(time)
    # Verify that we found the opposite apsis from the previous one.
    if apsis.kind not in [ApsisKind.Apocenter, ApsisKind.Pericenter]:
        raise Error('Parameter "apsis" contains an invalid "kind" value.')
    if next.kind + apsis.kind != 1:
        raise InternalError()
    return next

def RotateVector(rotation, vector):
    """Applies a rotation to a vector, yielding a rotated vector.

    This function transforms a vector in one orientation to a vector
    in another orientation.

    Parameters
    ----------
    rotation : RotationMatrix
        A rotation matrix that specifies how the orientation of the vector is to be changed.
    vector : Vector
        The vector whose orientation is to be changed.

    Returns
    -------
    Vector
        A vector in the orientation specified by `rotation`.
    """
    return Vector(
        rotation.rot[0][0]*vector.x + rotation.rot[1][0]*vector.y + rotation.rot[2][0]*vector.z,
        rotation.rot[0][1]*vector.x + rotation.rot[1][1]*vector.y + rotation.rot[2][1]*vector.z,
        rotation.rot[0][2]*vector.x + rotation.rot[1][2]*vector.y + rotation.rot[2][2]*vector.z,
        vector.t
    )


def Rotation_EQJ_ECL():
    """Calculates a rotation matrix from equatorial J2000 (EQJ) to ecliptic J2000 (ECL).

    This is one of the family of functions that returns a rotation matrix
    for converting from one orientation to another.
    Source: EQJ = equatorial system, using equator at J2000 epoch.
    Target: ECL = ecliptic system, using equator at J2000 epoch.

    Returns
    -------
    RotationMatrix
        A rotation matrix that converts EQJ to ECL.
    """
    # ob = mean obliquity of the J2000 ecliptic = 0.40909260059599012 radians.
    c = 0.9174821430670688;    # cos(ob)
    s = 0.3977769691083922;    # sin(ob)
    return RotationMatrix([
        [ 1,  0,  0],
        [ 0, +c, -s],
        [ 0, +s, +c]
    ])
