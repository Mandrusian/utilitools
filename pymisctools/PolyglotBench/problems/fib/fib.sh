read n
a=0; b=1
for ((i=0; i<n; i++)); do
  t=$a; a=$b; b=$((t + b))
done
echo $a
