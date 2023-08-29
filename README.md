# City Maps

Recently I picked up interest again for Pinterest, a social media that I straight up refused to use due to their terrible website and their incredibly bad practice of forcing you to create an account and install an application (if you are on mobile) in order to view the content.
I don't really know why, but I decided to give it another try and I was quite surprised by the amount of interesting content that I found there.
It takes a while (such as with TikTok) but after a few like and a few saves you start to see things that really suit your interests.
One day, after scrolling for a while, I found a few images that reminded me of an old project I have published on GitHub only and that I am not completely satisfied with (this is why it is not on my Instagram profile): [Minimalistic Maps](https://github.com/lorossi/minimalistic-maps).

In short, the repository contains a script that generates maps of cities using the [OpenStreetMap](https://www.openstreetmap.org/) API and the [PIL](https://pillow.readthedocs.io/en/stable/), by plotting only certain elements of the city (benches, trees, banks, trash cans, etc.).
It gives a strange representation of cities, and you can really see the difference between countries; it was created because of my curiosity, but I never really used it for anything else.
Before completely giving up, I started working on an extension of the map generation that could produce "rounded" maps that looked a little bit hand-drawn, but I have never really bothered to finish it.
I spent a lot of time on it but I was never really satisfied with the outcome, so I abandoned it (as now, there's not even a README file), even forgetting that I had it on public.

However, I started thinking about it again, and a few ideas came quickly to my mind.

So, I decided to give it another try and this time I am quite happy not only with the result but also with the code:
first of all, I dropped completely the idea of using a library to interface with the OpenStreetMap API, as I decided to use the [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) and the [Nominatim API](https://wiki.openstreetmap.org/wiki/Nominatim) directly.
I can't deny that the OSM query language is way messy and beyond my understanding. At first, I reached out to my good friend ChatGPT to get some help with it, but with not much success; I found the even better StackOverflow and I was able to leech some knowledge from a brave user that needed the same help as me.

The maps are then drawn on an image, according to a set of rules that define their styles, including the colour of the buildings and the font used to write the name of the city;
I then made a few different styles, taking inspiration from some art styles and paintings.
Which one looks better, is up to you to decide.

I tried to implement a map-colouring algorithm leveraging the [Four colour theorem](https://en.wikipedia.org/wiki/Four_color_theorem), but I quickly found out how hard finding an exact solution for this is;
I then promptly implemented a simple greedy algorithm that works quite well.
A few buildings (less than 0.01% of the total) might have the same colour as a neighbour, but I think that this is not a big deal.

I would love to try this out on a pen plotter, but I don't have one (yet).
Building one might really be a good idea for a future project.

## Output

A few outputs that I like:

Make sure to also check my [Instagram profile](https://www.instagram.com/lorossi97/) and navigate the repo (the folders [maps](/maps/) and [composed](/composed/) for more images.

## Code

The repo contains 3 different Python scripts:

- `city.py`, generating a fixed set of cities
- `city-cli.py`, generating a city based on a command line argument
- `compose.py`, generating a collage of cities and saving it as a single image

### Usage of `city.py`

In order to start using the script, the following steps are required:

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

- Asher Punk by Allouse.Studio
- Astida Scripto by FreshTypeINK
- Bauhaus by ALLTYPE
- Beautiful People by Billy Argel Fonts
- DeStijl by Garrett Boge
- HotSnow by Alit Design
- Kitschy Retro by Creative Fabrica
- Love Nature by Joe Dawson
- Moon by Jack Harvatt
- NUSAR by Free Fonts
- Pastel by Vladimir Creative Fabrica
- Tropical Asian by Konstantine Studio
- Raleway by Matt McInerney
- Roquen by Letterhend Studio
- Vincent by Macromedia
