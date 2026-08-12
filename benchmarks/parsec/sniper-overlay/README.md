# Sniper PARSEC overlay

These files adapt PARSEC 2.1 to the Sniper simulator. They are derived from
the official Sniper benchmarks repository at commit
`ba6004fd2b251be0ee5fc9e5d77374f1d4c80317`:

https://github.com/snipersim/benchmarks/tree/ba6004fd2b251be0ee5fc9e5d77374f1d4c80317/parsec/parsec-2.1

HotPROTON additionally links the shared Heartbeats library from the global
`gcc-sniper` build configuration because its PARSEC patches call that API.
