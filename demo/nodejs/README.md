# JavaScript examples for Node.js

The source file
[`astronomy.js`](../../source/js/astronomy.js)
works as a Node.js module. Download the file into your project directory.
Then in your own source file, do this:

```javascript
const Astronomy = require('astronomy.js');
```

or install the package with `npm i astronomy-engine` and:

```typescript
import { SearchMoonQuarter } from 'astronomy-engine';
```

![Vanilla JS](../vanillajs.png) There are no external dependencies!
Astronomy Engine is completely self-contained, and it always will be.

(By the way, you can use the same file `astronomy.browser.js` for
[astronomy calculations inside the browser](../browser/).)

---

### [Culmination](culminate.js)
Finds when the Sun, Moon, and planets reach their highest position in the sky on a given date,
as seen by an observer at a specified location on the Earth.
Culmination is also the moment a body crosses the *meridian*, the imaginary semicircle
in the sky that passes from due north on the horizon, through the zenith (straight up),
and then toward due south on the horizon.

### [Equator of Date](equator_of_date.js)
Given the right ascension and declination of a star,
expressed in J2000 coordinates, converts those coordinates
to right ascension and declination expressed in the Earth's
equator at any given date and time. This example illustrates
how to use rotation matrices to convert one coordinate system
to another.

### [Horizon Intersection](horizon.js)
This is a more advanced example. It shows how to use coordinate
transforms to find where the ecliptic intersects with an observer's
horizon at a given date and time.

### [Lunar Eclipse](lunar_eclipse.js)
Calculates details about the first 10 partial/total lunar eclipses
after the given date and time.

### [Moon Phase Calculator](moonphase.js)
This example shows how to determine the Moon's current phase,
and how to predict when the next few quarter phases will occur.

### [Positions](positions.js)
Calculates equatorial and horizontal coordinates of the Sun, Moon, and planets.

### [Rise/Set](riseset.js)
Shows how to calculate sunrise, sunset, moonrise, and moonset times.

### [Seasons](seasons.js)
Calculates the equinoxes and solstices for a given calendar year.

### [Triangulate](triangulate.js)
Given the geographic coordinates of two observers, and angular
directions they are looking in, determines geographic coordinates
of the point they are both looking at. This example demonstrates
use of the geoid functions `VectorObserver` and `ObserverVector`
that convert between geographic coordinates and vectors.

---

# [API Reference](../../source/js/)
Complete documentation for all the functions and types available
in the JavaScript version of Astronomy Engine.
