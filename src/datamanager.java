import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.*;

class DataManager {

    /** Resolved against the directory you run java from, so it works either
     *  from the repo root or from src/. */
    private static final Path DB = findDb();

    private static Path findDb() {
        Path p = Paths.get("data", "lehigh_valley_prices.db");
        if (!p.toFile().exists()) {
            p = Paths.get("..", "data", "lehigh_valley_prices.db");
        }
        return p.toAbsolutePath().normalize();
    }

    /** SQLite has no server, user, or password -- the URL is just the file.
     *  open_mode=1 is SQLITE_OPEN_READONLY; drop it if you need to write.
     *  (conn.setReadOnly(true) after connecting throws on this driver.) */
    static Connection connect() throws SQLException {
        return DriverManager.getConnection("jdbc:sqlite:" + DB + "?open_mode=1");
    }

    public static void main(String args[]) {

        try (Connection conn = connect()) {

            System.out.println("Connected to " + DB);
            System.out.println("SQLite " + conn.getMetaData().getDatabaseProductVersion());

            // Always use a PreparedStatement with ? placeholders rather than
            // concatenating values into the SQL string.
            String sql =
                "SELECT hospital_id, payer_name, plan_name, negotiated_dollar " +
                "FROM v_rate " +
                "WHERE service_code = ? " +
                "  AND negotiated_dollar IS NOT NULL " +
                "ORDER BY negotiated_dollar";

            String code = (args.length > 0) ? args[0] : "72148";

            try (PreparedStatement ps = conn.prepareStatement(sql)) {
                ps.setString(1, code);

                try (ResultSet rs = ps.executeQuery()) {
                    System.out.printf("%n%-10s %-26s %-22s %10s%n",
                            "HOSPITAL", "PAYER", "PLAN", "RATE");
                    int n = 0;
                    while (rs.next()) {
                        System.out.printf("%-10s %-26s %-22s %10.2f%n",
                                rs.getString("hospital_id"),
                                rs.getString("payer_name"),
                                rs.getString("plan_name"),
                                rs.getDouble("negotiated_dollar"));
                        n++;
                    }
                    System.out.println("\n" + n + " rates for service " + code);
                }
            }
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
