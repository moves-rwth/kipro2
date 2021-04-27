# ------------------------------  BMC ------------------------------------

# Geometric Loop
c = """
   nat c;
   nat f;

   while(f=1){
   {f := 0}[0.5]{c := c+1}
   }
"""

# Recall: We disprove wp[c](post) <= pre

post = "c"
pre = "c + 0.99"

#kipro2: SAT. Model:
# f := 1
# c := 6
#Refute. (Unrolling_depth = 11. Number formulae = 103)
#------ Statistics ------
#Total time = 0.06 s.
#Time for computing formulae = 0.06 s.
#Time for sat checks: 0.0 s.




post = "c"
pre = "c + 0.99999999"
# kipro2: SAT. Model:
#  f := 1
# c := 9
# Refute. (Unrolling_depth = 32. Number formulae = 628)
# ------ Statistics ------
# Total time = 0.3 s.
#  Time for computing formulae = 0.27 s.
#  Time for sat checks: 0.01 s.



post = "c"
pre = "c + 1"
#Diverge



# ------------------------------

# Simplified BRP
c = """
   # Adapted from Jip's MA
   # The number of packages to send
   nat toSend;

   # Number of packages sent
   nat sent;

   # The maximal number of retransmission tries
   nat maxFailed;

   # The number of failed retransmission tries for current package
   nat failed;

   # Count the total number of failed retransmissions
   nat totalFailed; # Initially totalFailed=0

   while(failed < maxFailed & sent < toSend){
      {
         # Transmission of current packages successful
         failed := 0;
         sent := sent + 1;
      }
      [0.9]
      {
         # Transmission not successful
         failed := failed +1;
         totalFailed := totalFailed +1;
      }
   }
"""

# Recall: We disprove wp[c](post) <= pre

post = "[sent = toSend]*totalFailed"

pre = "[failed < maxFailed & sent < toSend & failed = 0 & sent=0 & (maxFailed <= toSend) & totalFailed = 0] * (maxFailed*0.4) " \
      \
      "+ [not (failed < maxFailed & sent < toSend & failed=0 & sent=0 & (maxFailed <= toSend) & totalFailed = 0)]*\\infty"

#kipro2: SAT. Model:
# maxFailed := 2
# totalFailed := 0
# failed := 0
# sent := 0
# toSend := 11
#Refute. (Unrolling_depth = 14. Number formulae = 1935)
#------ Statistics ------
#Total time = 10.22 s.
# Time for computing formulae = 1.73 s.
# Time for sat checks: 8.47 s.



# ------------------------------ K - Induction ------------------------------

# Geometric Loop
c = """
   nat c;
   nat f;

   while(f=1){
   {f := 0}[0.5]{c := c+1}
   }
"""

# Recall: We prove wp[c](post) <= pre

post = "c"
pre = "[f=1]*(c + 1) + [not (f=1)]*c"
# Property is 1-inductive. (Number formulae = 8)
# ------ Statistics ------
# Total time = 0.01 s.
#  Time for computing formulae = 0 s.
#  Time for sat checks: 0.01 s.



post = "c"
pre = "c + 1"
# Property is 2-inductive. (Number formulae = 18)
# ------ Statistics ------
# Total time = 0.02 s.
#  Time for computing formulae = 0.01 s.
#  Time for sat checks: 0.01 s.




# ------------------------------

# Simplified BRP
c = """
   # Adapted from Jip's MA
   # The number of total packages to send
   nat toSend;

   # Number of packages sent
   nat sent;

   # The maximal number of retransmission tries
   nat maxFailed;

   # The number of failed retransmission tries
   nat failed;

   while(failed < maxFailed & sent < toSend){
      {
         # Transmission of current packages successful
         failed := 0;
         sent := sent + 1;

      }
      [0.9]
      {
         # Transmission not successful
         failed := failed +1;
      }
   }
"""

# Recall: We prove wp[c](post) <= pre

# 5-inductive
post = "[failed=maxFailed]"
pre = "[sent = 0 & failed = 0 & failed < maxFailed & toSend <= 4] * 0.35 + [not (sent = 0 & failed = 0 & failed < maxFailed & toSend <= 4)]*1"

# Property is 5-inductive. (Number formulae = 263)
# ------ Statistics ------
# Total time = 0.19 s.
#  Time for computing formulae = 0.16 s.
#  Time for sat checks: 0.02 s.


# Drop sent=0 & failed=0
post = "[failed=maxFailed]"
pre = "[failed < maxFailed & toSend <= 4] * 0.35 + [not (failed < maxFailed & toSend <= 4)]*1"

# Property is 5-inductive. (Number formulae = 313)
# ------ Statistics ------
# Total time = 0.21 s.
#  Time for computing formulae = 0.18 s.
#  Time for sat checks: 0.02 s.


# Not 5-inductive (and probably not k-inductive for any k)
pre_infty = "[sent = 0 & failed = 0 & failed < maxFailed & toSend <= 4] * 0.35 + [not (sent = 0 & failed = 0 & failed < maxFailed & toSend <= 4)]*\\infty"



# 2-inductive
post = "failed"
pre = "[sent < toSend & failed < maxFailed & maxFailed*5 < toSend] * (toSend*0.2) + [not (sent < toSend & failed < maxFailed & maxFailed*5 < toSend)]*\\infty"

# Property is 2-inductive. (Number formulae = 34)
# ------ Statistics ------
# Total time = 0.03 s.
#  Time for computing formulae = 0.02 s.
#  Time for sat checks: 0.01 s.




# ------------------------------

# Uniform distribibution from fair coin flips
c = """
# Adapted form http://www-i2.informatik.rwth-aachen.de/pub/index.php?type=download&pub_id=1233, which is adapted from
# Jérémie Lumbroso. Optimal Discrete Uniform Generation from Coin Flips, and Applications.
# In: CoRR abs/1304.1916 (2013).

# We want to model uniform(elow,...,ehigh)
nat elow;
nat ehigh; # Initially elow <= ehigh

nat c; # Initially 0. Stores result

nat n; # Initially n=ehigh-elow + 1
nat v; # Initially v=1

nat running; # Initially 0
nat i; # auxiliary variable for array positions in specifications

while(running = 0){

    v := 2*v;
    {c := 2*c+1}[0.5]{c := 2*c};
    if((not (v<n))){
        if((not (n=c)) & (not (n<c))){ # terminate
            running := 1
        }{
            v := v-n;
            c := c-n;
        }
    }{
        skip
    }

    # On termination, determine correct index
    if((not (running = 0))){
       c := elow + c;
    }{
       skip
    }
} """

# Recall: We prove wp[c](post) <= pre

post = "[c=i]"
pre = "[elow+4=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*0.2 " \
      "+ [not (elow+4=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1"

# (ehigh + 1)/2

# (ehigh + elow)/2 + 1

# Property is 5-inductive. (Number formulae = 40560)
# ------ Statistics ------
# Total time = 57.27 s.
#  Time for computing formulae = 47.18 s.
#  Time for sat checks: 10.08 s.




c = """
      # Adapted from
      #Joe Hurd, Annabelle McIver, Carroll Morgan:
      #Probabilistic Guarded Commands Mechanized in HOL. Electron. Notes Theor. Comput. Sci. 112: 95-111 (2005)

        nat i;
        nat n; # Does not need to be initialized
        nat d;

        #while(1<i){
        #    n:=i;
        #    while(0<n){
        #        {d:=0}[0.5]{d:=1};
        #        i:=i-d;
        #        n:=n-1;
        #    }
        #}

        nat phase; # Initially 0
        while(1<i || phase=1){
            if(phase=0){
                n:=i;
                phase:=1;
            }{
                if(0<n){
                    {d:=0}[0.5]{d:=1};
                    i:=i-d;
                    n:=n-1;
                }{ #leave inner loop
                    phase:=0;
                }
            }
        }

    """

# Hurd, McIver, and Morgan prove:
# [i=1] + [1 < i]*2/3 <= wlp[c]([i=1])

# Recall: We prove wp[c](post) <= pre
# The following is 5-inductive
post = "[i=1]"
pre = "[1<i & i<3 & phase=0] * (2/3) + [not (1<i & i < 3 & phase=0)]*1"
# Property is 5-inductive. (Number formulae = 1775)
# ------ Statistics ------
# Total time = 1.64 s.
#  Time for computing formulae = 1.59 s.
#  Time for sat checks: 0.04 s.

# For i<4, it seems to get hard ...
