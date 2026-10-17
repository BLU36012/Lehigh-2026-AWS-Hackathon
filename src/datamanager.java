import java.sql.*;

class DataManager {
    public static void main(String args[]) {
        
        try {
            
        }
        catch(SQLException e) {
            System.out.println(e.getMessage());
            System.out.println(e.getStackTrace());
        }
        catch(Exception e) {
            System.out.println("Grievous error");
            // this shouldn't ever hit
        }
    }

}