# Notes

- query to get the city boundaries:

```overpass
[out:json];
relation[name="Milano"][type="boundary"][admin_level=8](area:3600044915);
out geom;
```

- query to get the city buildings:

```overpass
[out:json];
(
  way["building"](around:{dist},{lat},{lon});
  relation["building"](around:{dist},{lat},{lon});
);
out geom;
```

- colour palette
  - <https://coolors.co/154084-9d2719-ba6e19-d7b418-e2d183-e8dfb8-ededed-222222>
