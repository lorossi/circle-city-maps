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
