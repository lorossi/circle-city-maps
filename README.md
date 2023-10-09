# Circle City Maps

<p align="center">
  <img width="400" height="400" src="/output/Milan-Bauhaus.png">
  <img width="400" height="400" src="/output/Turin-Black_and_White.png">
</p>

<p align="center">
  <img width="400" height="400" src="/output/Florence-Pitch_Black.png">
  <img width="400" height="400" src="/output/Rome-Jungle.png">
</p>

> Why do I feel like I am in a museum gift shop?

## Some History

Recently I picked up interest again for Pinterest, a social media that, back in the day, I straight up refused to use due to its terrible website and its incredibly bad practice of forcing you to create an account and install an application *(if you are fool enough to use a mobile browser)* before letting you see the content.
I don't know why, but a couple of months ago I decided to give it another try and I was quite surprised by the amount of interesting content that I found there.
It takes a while to get a customized home page, but after a few likes and a few saves you start to see things that suit your interests.

Of course, it did not take long to see posts about graphic design, Ferrari cars *(mostly F40s, weirdly enough)*, and generative art.

One day, after scrolling for a while, I found a few images that reminded me of an old project I have published on GitHub only and that I am not completely satisfied with *(this is why it is not on my Instagram profile)*: [Minimalistic Maps](https://github.com/lorossi/minimalistic-maps).

In short, that repository contains a script that generates maps of cities by plotting only certain elements of the city *(such as benches, trees, banks, trash cans, etc...)* via the [OpenStreetMap](https://www.openstreetmap.org/) API and the [PIL](https://pillow.readthedocs.io/en/stable/) library.
Cities get represented in weird ways, and you can notice their various landmarks and features without having to draw them explicitly.

My curiosity fuelled this project, but it never really saw the light of day, as I was never satisfied with the outcome.

Before completely giving up, I started working on an extension of the map generation that could produce *"rounded"* maps that looked a little bit hand-drawn, but I once more was never really bothered to finish it, despite having put quite the effort into it:
I was never really satisfied with the outcome, so I abandoned it *(as now, there's not even a README file)*, even forgetting that I had it on my computer.

However, thanks to the aforementioned social platform, I found a few images that reminded me of that project and I decided to give it another try:
this time I was able to get a few good results, and I am quite happy with them.

The buildings, streets, parks and all the other features of the maps are sourced directly from [Open Street Maps](https://www.openstreetmap.org/), which is quite accurate and detailed *(to my surprise, given that is a less-known alternative to Google Maps and it's completely community-driven)*.
I have never put much trust into OSM, since the competing Google Maps has always worked well enough for me, but I was quite surprised by the sheer amount of detail that OSM has:
all the buildings are correctly mapped and categorized, the interest points are all there, and the streets are all correctly placed (not to mention all the street lights, benches, trash cans, ...).

At first, I tried interfacing with the OpenStreetMap API using a library, but I quickly found out that it was not really what I was looking for, since it was too complex, not flexible and quite slow *(I have no idea why, but it took a couple of minutes to get the data for a single city)*.
I quickly dropped it, as I decided to use the [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) and the [Nominatim API](https://wiki.openstreetmap.org/wiki/Nominatim) directly.

I can't deny that the OSM query language is way messy and beyond my understanding. At first, I reached out to my good old friend *ChatGPT* to get some help with it, but with not much success; I found the even better *StackOverflow* and I was able to leech some knowledge from a brave user who needed the same help as me.

The only thing that I don't like about the OSM queries is how the data is returned: interest points are returned as nodes, while streets, parks, and water areas are returned sometimes as ways, sometimes as relations:
this makes complete sense, as you cannot always represent the latter as single nodes; but why some are ways and some are relations is beyond my understanding.
My guess is that "ways" are just "building blocks" that can be used to build everything else, from shorelines to roundabouts, and that relations are used to group them together.
But why return a mixed set of ways and relations? Couldn't they just return everything as relations?
The relations contain `inner` and `outer` ways, which are used to represent the inner and outer boundaries of the relation itself:
for examples, buildings with an hollow courtyard are represented as a relation with an outer way and an inner way.
On the other hand, if a buildings has no hollow sections, it is represented as a single way, and the same goes for parks and water areas.
Finally, the ways in each relation are not necessarily ordered *(this has been an issue in mapping Budapest, where the river was messy and there was no way of drawing it as a polygon without having to re-organize the ways)*, so I lost quite a bit of time trying to figure out how to draw them correctly.

To get all the nodes, two different procedures must be used:

- one to extract the nodes from the relations
- one to extract the nodes from the ways

Then they can be merged together and used to draw the map as polygons.

Each feature *(buildings, streets, parks, etc...)* is drawn on a separate layer and then merged together to form the final map.

The color of each feature is defined in by a style, which contains the description of the color for water area, parks, and streets, the palette for the buildings, and the font used to write the name of the city.
The project includes a few different styles: some of them are sampled from planets (*Moon* and *Mars*), others from paintings (*Mondrian* and *Starry Night*), while to make others I picked a few colours that looked good together and I tried to make something out of them (such as *Modern* and *Pastel*).
The fonts have all been picked from various sources on the internet, as they are demo versions or free to use for personal projects.

I tried to implement a map-colouring algorithm leveraging the [Four colour theorem](https://en.wikipedia.org/wiki/Four_color_theorem) to prevent neighbouring buildings from sharing the same colours, but I quickly found out how hard finding an exact solution for this is:
[this paper by Robertson, Sanders, Seymour and Thomas](https://thomas.math.gatech.edu/PAP/fcstoc.pdf) describes an algorithm able to solve the problem in quadratic time.

Well, **it turns out that this is kind of a complex problem** and implementing it would have been more time-consuming than I thought, so I chose to drop it and implement a greedy algorithm instead.

The greedy algorithm works as follows:

1. Find all the neighbours of each building
2. Sort the buildings by the number of neighbours
3. For each building, assign a colour that is not used by any of its neighbours
4. If no colour is available, fill the building with a random colour

The algorithm is applied multiple times *(about 50)*, and only the best outcome is used.
A few buildings *(less than 0.01% of the total)* might have the same colour as a neighbour, but I think that this is not a big deal: the buildings are small enough to not be noticed.
After spending quite some time on this idea, I then realized that you can barely notice the difference between the greedy algorithm and random colours, but hey, at least I tried.

After selecting colours for buildings and features, the map is finally drawn on an image: all these steps are taken care of by the `circle-city.py` script.

A CLI version of the script is also available, and it can be used to generate a single map from the command line: this is useful for... well... I don't know, but it felt weird to not make it since every aspect of the code was already there, ready to be parameterized (no hardcoded values have been used!).
It is found in the `city-cli.py` script.

Check the [Usage](#usage-of-circle-citypy) section for more information about the command line arguments.

Finally, the last script, (`compose.py`) can be used to compose multiple maps into a single image, which can be used as a poster or as a wallpaper.

I grouped the maps into 3 different categories:

- 9 biggest capitals of the EU
- 4 capitals of the Mediterranean area
- the 4 historic capitals of Italy *(Milan is a little bit cheeky, but after all, it was the capital of the Cisalpine Republic)*.

I didn't upload all the output (it's repetitive and, most of all, ~3GB of images), but you can find a subset of the output in the [output](/output/) folder and the following parts of the README.

## Final thoughts

- Using the Overpass API is better than using a library, even if I had to create data structures to represent the data and it is not flexible at all
- I would like to try to implement the map-colouring algorithm described in the paper, but I don't think that I will ever do it (unless in another project).
- An easier way of implementing the aforementioned algorithm would probably be with backtracking, but once again it's not worth the effort nor the time.
- Another thing that I would like is to try to print the maps (maybe the black and white ones) on a pen plotter, but sadly I don't own one of those.
- I am really satisfied with the result and could extend this to make square or rectangle-shaped maps to print as posters.

## Output

A few outputs that I like:

<p align="center">
  <img src="/output/Capitals-Black_and_White.png">
</p>
<p align="center">
  <img src="/output/Capitals-Cyberpunk.png">
</p>
<p align="center">
  <img src="/output/Capitals-Modern.png">
</p>
<p align="center">
  <img src="/output/Capitals-Mondrian.png">
</p>

<p align="center">
  <img src="/output/Italian-Capitals-Mars.png">
</p>

<p align="center">
  <img src="/output/Italian-Capitals-Moon.png">
</p>

<p align="center">
  <img src="/output/Mediterranean-Sea.png">
</p>

<p align="center">
  <img src="/output/Mediterranean-Sunset.png">
</p>

Make sure to also check my [Instagram profile](https://www.instagram.com/lorossi97/).

## Code

The repo contains 3 different Python scripts:

- `circle-city.py`, generating a fixed set of cities
- `city-cli.py`, generating a city based on a command line argument
- `compose.py`, generating a collage of cities and saving it as a single image

### Usage of `circle-city.py`

To start using the script, the following steps are required:

- Create a virtual environment

```bash
python3 -m venv venv
```

- Activate the virtual environment

```bash
source venv/bin/activate
```

- Install the required dependencies

```bash
pip install -r requirements.txt
```

- Run the script
  - `circle-city.py`: `python3 circle-city.py`
  - `city-cli.py`: `python3 city-cli.py`

The first script will generate a fixed set of cities (as now, the capitals of the EU and London), while the second one will generate a city based on a command line argument.
For more information about the command line arguments, please refer to the next section.

#### Example of usage

- Generate a map of the city of London, using the `Modern` style and saving it as `london.png` of size 1000x1000 pixels

```bash
python3 circle-city.py --city London --style Modern --output london.png --width 1000 --height 1000
```

- List all the available styles

```bash
python3 circle-city.py --list-styles
```

- View all command line arguments

```bash
python3 circle-city.py --help
```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

Fonts used:

- *Asher Punk* by *Allouse.Studio*
- *Astida Scripto* by *FreshTypeINK*
- *Bauhaus* by *ALLTYPE*
- *Celtic Sea by Art Designs* by *Sue*
- *DeStijl* by *Garrett Boge*
- *HotSnow* by *Alit Design*
- *Kitschy Retro* by *Creative Fabrica*
- *Love Nature* by *Joe Dawson*
- *Moon* by *Jack Harvatt*
- *NUSAR* by *Free Fonts*
- *Pastel* by *Vladimir Creative Fabrica*
- *Tropical Asian* by *Konstantine Studio*
- *Raleway* by *Matt McInerney*
- *Roquen* by *Letterhead Studio*
- *Vincent* by *Macromedia*
