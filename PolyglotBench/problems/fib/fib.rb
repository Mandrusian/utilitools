n = $stdin.read.strip.to_i
a, b = 0, 1
n.times { a, b = b, a + b }
puts a
