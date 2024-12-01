## Artix Linux optimize packages 
This repo has only makepkg file that will optimize the packages 
according to your system .
The packages will only optimize if you will build it from source.

## Reasons to create this repo

- Cachy os like performance on non systemd Artix by optimizing the
  packages

## Upcoming 
A python script that will clone the package repo extract the dependencies and build both pkg and its dependency with custom 
makepkf file .

## Need for Scipt
It is awful to manually clone pkg repo and its dependency repo and build them .
I also not found anything on artix forum that allow user to build 
pkg from source like u do with AUR i know we can use AUR on artix 
but when it come to core pkg artix maintains it own pkg that donot need systemd stuff 

## Suggestion 
If anyone knows how we can achieve such automation like aur on Artix plz tellme 😁.

## script current status 

- working on handling of recursive dependency

## Slow 

I am slow as sloth in working on this project so i myself dont   know when i will complete this.

## Reason script is not here 

because it is pretty messed up for now 
