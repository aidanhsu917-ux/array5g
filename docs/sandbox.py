import numpy as np

def main():
    center_freq = 2.1e9
    c = 299792458
    d = c/(2*center_freq)
    Nr = 2
    theta_i = -np.pi/2
    s = np.exp(-2j * np.pi * d * center_freq/c * np.arange(Nr) * np.sin(theta_i))
    print(s.shape)

    x = np.array([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    y = s.conj().T @ x
    print(y)

if __name__ == "__main__":
    main()