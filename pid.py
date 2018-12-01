class PID:
   def __init__(self, p_gain, i_gain, d_gain, min_i_error, max_i_error, now):
      self.last_error = 0.0
      self.last_time = now

      self.p_gain = p_gain
      self.i_gain = i_gain
      self.d_gain = d_gain
      
      self.min_i_error = min_i_error
      self.max_i_error = max_i_error

      self.i_error = 0.0
      
      self.last_output = 0
      
   def setIntegralMinMax(self, min_i_error, max_i_error):
      self.min_i_error = min_i_error
      self.max_i_error = max_i_error
      
   def reinit(self, target, input, now):
      self.last_error = target - input
      self.i_error = self.max_i_error
      self.last_time = now

   def compute(self, input, target, now):
      dt = (now - self.last_time)

      #---------------------------------------------------------------------------
      # Error is what the PID algorithm acts upon to derive the output
      #---------------------------------------------------------------------------
      error = target - input

      #---------------------------------------------------------------------------
      # The proportional term takes the distance between current input and target
      # and uses this proportially (based on Kp) to control the ESC pulse width
      #---------------------------------------------------------------------------
      p_error = error

      #---------------------------------------------------------------------------
      # The integral term sums the errors across many compute calls to allow for
      # external factors like wind speed and friction
      #---------------------------------------------------------------------------
      self.i_error += (error + self.last_error) * dt
      
      if self.i_error > self.max_i_error:
          self.i_error = self.max_i_error
      elif self.i_error < self.min_i_error:
          self.i_error = self.min_i_error
      
      i_error = self.i_error
      print("\tPID - i error: {}, min: {}, max: {}".format(i_error, self.min_i_error, self.max_i_error))

      #---------------------------------------------------------------------------
      # The differential term accounts for the fact that as error approaches 0,
      # the output needs to be reduced proportionally to ensure factors such as
      # momentum do not cause overshoot.
      #---------------------------------------------------------------------------
      d_error = (error - self.last_error) / dt
      print("\tPID - d error: {}, last_error: {}, dt: {}".format(error, self.last_error, dt))
      
      #---------------------------------------------------------------------------
      # The overall output is the sum of the (P)roportional, (I)ntegral and (D)iffertial terms
      #---------------------------------------------------------------------------
      p_output = self.p_gain * p_error
      i_output = self.i_gain * i_error
      d_output = self.d_gain * d_error

      #---------------------------------------------------------------------------
      # Store off last input for the next differential calculation and time for next integral calculation
      #---------------------------------------------------------------------------
      self.last_error = error
      self.last_time = now
      
      print("\tPID - P: {0}, I: {1}, D: {2}".format(p_output, i_output, d_output))
      self.last_output = p_output + i_output + d_output
      
      return self.last_output