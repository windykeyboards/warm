# Warm
**W**indy keyboards **AR**duino package **M**anager

Warm is a Github-based package manager, promoting Arduino Development for your average hipster software developer. It's based on Python 3.7, so you best be up to date son.

## How to install
Warm requires only three things to set up

1. Clone (or fork) this repo
`git clone https://github.com/windykeyboards/warm.git`
2. Add the `warm` directory to your PATH
`export PATH=$PATH:cwd/warm`
3. Set your arduino dir path up
`export ARDUINO_DIR=/Users/windyboye/Arduino`

## How to use
Create your dependency file, listing all the warm-compatible libraries you're interested in

##### dependencies.warm
```properties
// Comments work in here, so write whatever you want

// Want a tag/release of a github repo? 
windykeyboards/butt-in: 1.0

// Want a specific branch?
windykeyboards/butt-in: master

// What about a commit hash? EZ
windykeyboards/butt-in: abc123thisisasha1hash
```

Next, all you need to do is tell your project to warm up
`python warm.py up`

Optionally, you could sort out an alias to make warming up easier
`alias warmup='python warm.py up'`

## Making a library warm-compatible
Piece of cake. Create a `.warm_properties` file in the root of the repository

##### .warm_properties
```properties
// Properties file allowing this library to be used with warm
SRC_DIR=some_relative_dir
```

And even easier, if your source files are in the root of the repository, it's already warm-compatible!
