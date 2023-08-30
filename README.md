# City Maps

<p align="center">
  <img width="400" height="400" src="/output/Milan-Bauhaus.png">
  <img width="400" height="400" src="/output/Turin-Black_and_White.png">
</p>

<p align="center">
  <img width="400" height="400" src="/output/Florence-Pitch_Black.png">
  <img width="400" height="400" src="/output/Rome-Jungle.png">
</p>

Recently I picked up interest again for Pinterest, a social media that, back in the day, I straight up refused to use due to its terrible website and its incredibly bad practice of forcing you to create an account and install an application *(if you are fool enough to use a mobile browser)* before letting you see the content.
I don't know why, but a couple of months ago I decided to give it another try and I was quite surprised by the amount of interesting content that I found there.
It takes a while to get a customized home page, but after a few likes and a few saves you start to see things that suit your interests.

Of course, it did not take long to see posts about graphic design, Ferrari cars *(mostly F40s, weirdly enough)*, and generative art.

One day, after scrolling for a while, I found a few images that reminded me of an old project I have published on GitHub only and that I am not completely satisfied with *(this is why it is not on my Instagram profile)*: [Minimalistic Maps](https://github.com/lorossi/minimalistic-maps).

In short, the repository contains a script that generates maps of cities using the [OpenStreetMap](https://www.openstreetmap.org/) API and the [PIL](https://pillow.readthedocs.io/en/stable/), by plotting only certain elements of the city *(such as benches, trees, banks, trash cans, etc...)*.
Cities get represented in weird ways, and you can see the difference between countries.

My curiosity fuelled this project, but it never really saw the light of day, as I was never really satisfied with the outcome.

Before completely giving up, I started working on an extension of the map generation that could produce *"rounded"* maps that looked a little bit hand-drawn, but I have never really bothered to finish it, despite having put quite the effort into it:
I was never really satisfied with the outcome, so I abandoned it *(as now, there's not even a README file)*, even forgetting that I had it on my computer.

However, thanks to the aforementioned social platform, I found a few images that reminded me of that project and I decided to give it another try:
this time I was able to get a few good results, and I am quite happy with them.

The buildings, streets, parks and all the other features of the maps are sourced directly from [Open Street Maps](https://www.openstreetmap.org/), which is quite accurate and detailed (to my surprise).
I have never put much trust into OSM, since the competing Google Maps has always worked well enough for me, but I was quite surprised by the number of details that OSM has:
all the buildings are correctly mapped and categorized, the interest points are all there, and the streets are all correctly placed.

At first, I tried interfacing with the OpenStreetMap API using a library, but I quickly found out that it was not really what I was looking for;
I quickly dropped it, as I decided to use the [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) and the [Nominatim API](https://wiki.openstreetmap.org/wiki/Nominatim) directly.

I can't deny that the OSM query language is way messy and beyond my understanding. At first, I reached out to my good old friend *ChatGPT* to get some help with it, but with not much success; I found the even better *StackOverflow* and I was able to leech some knowledge from a brave user who needed the same help as me.

The only thing that I don't like about the OSM queries is how the data is returned: interest points are returned as nodes, while streets, parks, and waterways are returned as relations:
this makes complete sense, as you cannot represent the latter features as single points.
Buildings, however, are sometimes returned as nodes and sometimes as relations, which not only makes the code a little bit more complicated than it should be but still confuses me.
Furthermore, buildings have `inner` and `outer` polygons, and I still don't understand what they are for despite having read the documentation.

However, getting all the nodes is as simple as making one *(or two, for buildings)* queries, and then extracting the data from the JSON response.

Each map is then drawn on an image, according to a set of rules that define their styles;
Each style defines the colours, the fonts, and the way the map is drawn.
The project includes a few different styles: some of them are sampled from planets (*Moon* and *Mars*), others from paintings (*Mondrian* and *Starry Night*), while to make others I picked a few colours that looked good together and I tried to make something out of them (such as *Modern* and *Pastel*).
The fonts have all been picked from websites, as they are demo versions or free to use for personal projects.

I tried to implement a map-colouring algorithm leveraging the [Four colour theorem](https://en.wikipedia.org/wiki/Four_color_theorem) to prevent neighbouring buildings from sharing the same colours, but I quickly found out how hard finding an exact solution for this is:
I found a [paper by Robertson, Sanders, Seymour and Thomas](https://thomas.math.gatech.edu/PAP/fcstoc.pdf) describing an algorithm able to solve the problem in quadratic time.

Well, it turns out that this is kind of a complex problem and implementing it would have been more time-consuming than I thought, so I chose to drop it and implement a greedy algorithm instead.

The greedy algorithm works as follows:

- Find all the neighbours of each building
- Sort the buildings by the number of neighbours
- For each building, assign the first available colour
- If no colour is available, fill the building with a random colour

The algorithm is repeated multiple times *(about 50)*, and only the best result is used.
A few buildings *(less than 0.01% of the total)* might have the same colour as a neighbour, but I think that this is not a big deal: the buildings are small enough to not be noticed.

After selecting colours for buildings and features, the map is finally drawn on an image: all these steps are taken care of by the `city.py` script.

A CLI version of the script is also available, and it can be used to generate a single map from the command line: this is useful for... well... I don't know, but it felt weird to not make it since every aspect of the code was already there, ready to be parameterized (no hardcoded values have been used!).
It is found in the `city-cli.py` script.

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
  <img src="/output/capitals_composed_black_and_white.png">
</p>
<p align="center">
  <img src="/output/capitals_composed_cyberpunk.png">
</p>
<p align="center">
  <img src="/output/capitals_composed_modern.png">
</p>
<p align="center">
  <img src="/output/capitals_composed_mondrian.png">
</p>

<p align="center">
  <img src="/output/italian-capitals-mars.png">
  <img src="/output/italian-capitals-moon.png">
</p>

<p align="center">
  <img src="/output/mediterranean_sea.png">
  <img src="/output/mediterranean_sunset.png">
</p>

Make sure to also check my [Instagram profile](https://www.instagram.com/lorossi97/).

## Code

The repo contains 3 different Python scripts:

- `city.py`, generating a fixed set of cities
- `city-cli.py`, generating a city based on a command line argument
- `compose.py`, generating a collage of cities and saving it as a single image

### Usage of `city.py`

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
  - `city.py`: `python3 city.py`
  - `city-cli.py`: `python3 city-cli.py`

The first script will generate a fixed set of cities (as now, the capitals of the EU and London), while the second one will generate a city based on a command line argument.
For more information about the command line arguments, please refer to the next section.

#### Example of usage

- Generate a map of the city of London, using the `Modern` style and saving it as `london.png` of size 1000x1000 pixels

```bash
python3 city.py --city London --style Modern --output london.png --width 1000 --height 1000
```

- List all the available styles

```bash
python3 city.py --list-styles
```

- View all command line arguments

```bash
python3 city.py --help
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
