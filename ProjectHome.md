Google Maps gives you [API](http://code.google.com/apis/maps/documentation/reference.html#GTileLayerOverlay) for adding additional map layers. This software implements a map tile server for a heatmap layer.

![http://static.whit537.org/2008/heatmap-0.2.png](http://static.whit537.org/2008/heatmap-0.2.png)


---


## Gheat for ... ##

<a href='http://code.google.com/p/gheat-ae/'>Gheat for App Engine</a>

<a href='http://code.google.com/p/gheat/downloads/list'>Gheat for Aspen (<b>original version</b>)</a>

<a href='http://sixpak.org/vince/source/gheat/'>Gheat for CGI (Apache, MongoDB)</a>

<a href='http://github.com/robertrv/django-gheat'>Gheat for Django</a>

<a href='http://jjguy.com/heatmap/'>Gheat for Google Earth (and offline use in general)</a>

<a href='http://www.codeproject.com/KB/web-image/GHeat_Net.aspx'>Gheat for .NET</a>

<a href='http://github.com/amccollum/pyheat'>Gheat for OpenGL and CherryPy</a>

<a href='https://github.com/bigkraig/pylons_gheat'>Gheat for Pylons</a>

<a href='https://github.com/varunpant/GHEAT-JAVA'>Gheat for Java</a>


---


## Competitors ##

http://www.heatmaptool.com/

http://www.heatmapapi.com/


---



## Examples ##

<i>Please tell me (chad@zetaweb.com) if you'd like a link here.</i>

<b><a href='http://earth911.com/'>Earth911</a> uses gheat to show <a href='http://labs.earth911.com/heatmap/'>real-time recycling searches</a>.<br>
<br>
<b><a href='http://benosteen.wordpress.com/'>Ben O'Steen</a> made a <a href='http://benosteen.wordpress.com/2011/07/26/student-property-heatmap/'>student property heatmap</a>.<br>
<br>
<b><a href='http://www.tada.com/'>Tada</a> is using pylons_gheat to <a href='http://heatmap.tada.com/'>visualize sales</a>.<br>
<br>
<b><a href='http://www.wheredoyougo.net/'>Where Do You Go</a></b> is using gheat-ae to visualize FourSquare checkins.<br>
<br>
<b><a href='http://www.numberinvestigator.com/'>NumberInvestigator</a></b> is using gheat (with portions ported to PHP) to generate <a href='http://trends.numberinvestigator.com/'>hourly maps of telemarketing victims</a>.<br>
<br>
<b><a href='http://www.colorofchange.org/'>Color of Change</a></b> used gheat to visualize <a href='http://stories.colorofchange.org/'>stories of what Obama's election meant to voters</a> and how they participated in the campaign.<br>
<br>
<b><a href='http://vistrac.com/'>VisTrac</a></b> is using gheat to visualize <a href='http://vistrac.com/account/clicks/July-2009'>clicks on web pages</a>.<br>
<br>
<b><a href='http://vort.org/'>Russell Neches</a></b> is using gheat to visualize <a href='http://vort.org/media/data/crashes.html'>auto and bike accidents in Davis, CA</a>. The data is parsed from about 10,000 raw police reports.<br>
<br>
<b><a href='http://kurage.kilo.jp/heat'>Yvan Girard</a></b> is using gheat to show Twitter activity in and around Tokyo.<br>
<br>
<b><a href='http://www.honeynet.org.au/'>The Australian Honeynet Project</a></b> is using gheat to visualize the <a href='http://www.honeynet.org.au/?q=node/41'>origin of spam that gets caught in their SensorNET honeypots</a>.<br>
<br>
<b><a href='http://www.confickerworkinggroup.org/'>The Conficker Working Group</a></b> is using gheat to track the <a href='http://www.confickerworkinggroup.org/wiki/pmwiki.php/ANY/InfectionDistribution'>spread of the Conficker worm</a>.<br>
<br>
<img src='http://geoip.arpatubes.net/conficker_au.gif' />

This is an animated heatmap of the conficker botnet as found in Australia (one frame a day, unique IPs per frame, with data from the end of January through June, 2009). This was produced using a heavily modified gheat. Here's <a href='http://geoip.arpatubes.net/conficker/'>a Flash example</a>.<br>
<br>
<hr />

<h2><a href='http://www.zetadev.com/software/gheat/0.2/__/doc/html/'>Full Documentation</a></h2>

<h2>How it Works</h2>

This is a standalone web app that responds to URLs of the form<br>
<br>
<pre><code>/&lt;color_scheme&gt;/&lt;zoom&gt;/&lt;x&gt;,&lt;y&gt;.png<br>
</code></pre>

with 256px by 256px images like this:<br>
<br>
<img src='http://static.whit537.org/2008/4,6-again.png' />

You tell Google Maps (via their API) to place these images over your embedded map. The images are increasingly transparent as the zoom level increases, so they make a nice overlay.<br>
<br>
<hr />


<h2>Dependencies</h2>

<ul><li><a href='http://www.python.org/'>Python 2.5</a> (needs sqlite)<br>
</li><li><a href='http://www.pygame.org/'>Pygame 1.8.1</a> or <a href='http://www.pythonware.com/products/pil/'>PIL</a>
</li><li><a href='http://www.zetadev.com/software/aspen/'>Aspen 0.8</a> (Python webserver)</li></ul>

<h2>A Word about Backends</h2>

<ul><li>Pygame is three or four times faster than PIL.<br>
</li><li>Pygame is three or four times harder to install than PIL.<br>
</li><li><a href='http://www.zetadev.com/software/gheat/0.2/__/doc/html/installation.html'>Get Gheat working</a> with PIL first, then install Pygame.<br>
</li><li>You need Pygame 1.8.1 (saving to PNG was <a href='http://pygame.motherhamster.org/bugzilla/show_bug.cgi?id=13'>broken in 1.8.0</a>)<br>
</li><li>You need to install <a href='http://numpy.scipy.org/'>numpy</a> before you can use Pygame.</li></ul>

<hr />

<a href='http://www.zetadev.com/software/gheat/0.2/__/doc/html/'>Full documentation</a> is available.