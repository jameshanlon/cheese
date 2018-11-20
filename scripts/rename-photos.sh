#!/usr/bin/env bash
count=1
for i in *.jpg; do
  new=$(printf "%03d.jpg" "$count")
  mv -i -- "$i" "$new"
  let count=count+1
done
