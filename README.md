# CS6120 Lesson 3 Local Analysis and Optimizations

## Description

This repository implements two optimizations:
- Dead code elimination (DCE): `dce.py`
- Local value numbering (LVN): `lvn.py`
  - Constant propagation
  - Sub-expression elimination
  - Constant folding

## Run

Run DCE pass:
```
bril2json < *.bril | python dce.py | bril2txt
bril2json < *.bril | python dce.py | brili -p # profile dynamic instr count
```
Default DCE is local optimization. To run global DCE, add `-g`:
```
bril2json < *.bril | python dce.py -g | bril2txt
```

Run LVN Pass
```
bril2json < *.bril | python lvn.py | bril2txt
bril2json < *.bril | python lvn.py | brili -p # profile dynamic instr count
```


Run both:
```
bril2json < *.bril | python dce.py | python lvn.py | bril2txt
```

## Test

This repository includes two test folders for both optimizations. To run a test:
```
turnt tdce/*.bril
turnt lvn/*.bril
``` 

