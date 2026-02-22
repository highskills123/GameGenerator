"""
Demo script showing what Aibase can do
This doesn't require an API key - just shows examples
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         Aibase Demo - Sample Outputs                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Example 1: "Create a function that checks if a number is prime"
Language: Python
────────────────────────────────────────────────────────────────────────────────
def is_prime(n):
    '''
    Check if a number is prime.
    
    Args:
        n (int): The number to check
        
    Returns:
        bool: True if n is prime, False otherwise
    '''
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Check odd divisors up to sqrt(n)
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

# Example usage
print(is_prime(17))  # True
print(is_prime(4))   # False
────────────────────────────────────────────────────────────────────────────────


Example 2: "Create a function that reverses a string"
Language: JavaScript
────────────────────────────────────────────────────────────────────────────────
/**
 * Reverse a string
 * @param {string} str - The string to reverse
 * @returns {string} The reversed string
 */
function reverseString(str) {
    return str.split('').reverse().join('');
}

// Alternative implementation without built-in methods
function reverseStringManual(str) {
    let reversed = '';
    for (let i = str.length - 1; i >= 0; i--) {
        reversed += str[i];
    }
    return reversed;
}

// Example usage
console.log(reverseString('hello'));  // 'olleh'
────────────────────────────────────────────────────────────────────────────────


Example 3: "Create a binary search function"
Language: Java
────────────────────────────────────────────────────────────────────────────────
public class BinarySearch {
    /**
     * Perform binary search on a sorted array
     * 
     * @param arr Sorted array to search
     * @param target Value to find
     * @return Index of target, or -1 if not found
     */
    public static int binarySearch(int[] arr, int target) {
        int left = 0;
        int right = arr.length - 1;
        
        while (left <= right) {
            int mid = left + (right - left) / 2;
            
            if (arr[mid] == target) {
                return mid;
            } else if (arr[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        
        return -1; // Not found
    }
    
    // Example usage
    public static void main(String[] args) {
        int[] numbers = {1, 3, 5, 7, 9, 11, 13};
        System.out.println(binarySearch(numbers, 7));  // Output: 3
    }
}
────────────────────────────────────────────────────────────────────────────────


Example 4: "Create a REST API endpoint for user authentication"
Language: TypeScript
────────────────────────────────────────────────────────────────────────────────
import express, { Request, Response } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';

const router = express.Router();

interface LoginRequest {
    email: string;
    password: string;
}

/**
 * User authentication endpoint
 * POST /api/auth/login
 */
router.post('/auth/login', async (req: Request, res: Response) => {
    try {
        const { email, password }: LoginRequest = req.body;
        
        // Validate input
        if (!email || !password) {
            return res.status(400).json({
                error: 'Email and password are required'
            });
        }
        
        // Find user in database (example - implement your own logic)
        const user = await findUserByEmail(email);
        
        if (!user) {
            return res.status(401).json({
                error: 'Invalid credentials'
            });
        }
        
        // Verify password
        const isValidPassword = await bcrypt.compare(password, user.passwordHash);
        
        if (!isValidPassword) {
            return res.status(401).json({
                error: 'Invalid credentials'
            });
        }
        
        // Generate JWT token
        const token = jwt.sign(
            { userId: user.id, email: user.email },
            process.env.JWT_SECRET!,
            { expiresIn: '24h' }
        );
        
        res.json({
            success: true,
            token,
            user: {
                id: user.id,
                email: user.email,
                name: user.name
            }
        });
        
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({
            error: 'Internal server error'
        });
    }
});

export default router;
────────────────────────────────────────────────────────────────────────────────


╔══════════════════════════════════════════════════════════════════════════════╗
║                            How to Use Aibase                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

1. Install dependencies:
   pip install -r requirements.txt

2. Install and start Ollama (https://ollama.com):
   ollama pull qwen2.5-coder:7b

3. Run in interactive mode:
   python aibase.py

4. Or use directly:
   python aibase.py -d "your description here" -l python

For more examples and details, see:
- README.md - Full documentation
- QUICKSTART.md - Quick start guide
- examples.py - Code examples

Supported languages (21):
Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, PHP, Ruby, Swift, Kotlin,
Flutter/Dart, Dart, React Native,
Flame, Flame Complete Game, Flame Game Component,
Game Sprite Asset, Game Animation Asset, Game Tilemap
""")
