from sklearn.linear_model import LinearRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

# Sample dataset (replace this with your actual dataset)
queries = [ "SELECT c.*, cl.nom, cl.adresse FROM Commande c JOIN Client cl ON c.id_client = cl.id_client" , 
"SELECT lc.*, c.id_commande, p.nom_produit FROM Ligne_Commande lc JOIN Commande c ON lc.id_commande = c.id_commande JOIN Produit p ON lc.id_produit = p.id_produit " ,
"SELECT * FROM Commande WHERE id_client = 2" , 
"SELECT a.*, p.nom_produit, f.nom_fournisseur FROM Approvisionnement a JOIN Produit p ON a.id_produit = p.id_produit JOIN Fournisseur f ON a.id_fournisseur = f.id_fournisseur" , 
"SELECT c.id_client, c.nom, c.adresse, SUM(lc.quantite) AS total_produits_vendus FROM Client c JOIN Commande cmd ON c.id_client = cmd.id_client JOIN Ligne_Commande lc ON cmd.id_commande = lc.id_commande GROUP BY c.id_client, c.nom, c.adresse" , 
"SELECT c.id_client, c.nom, c.adresse, COALESCE(total_produits_vendus, 0) AS total_produits_vendus FROM Client c LEFT JOIN ( SELECT cmd.id_client, SUM(lc.quantite) AS total_produits_vendus FROM Commande cmd JOIN Ligne_Commande lc ON cmd.id_commande = lc.id_commande GROUP BY cmd.id_client ) total ON c.id_client = total.id_client",
"SELECT p.nom_produit, f.nom_fournisseur FROM Produit p JOIN Approvisionnement a ON p.id_produit = a.id_produit JOIN Fournisseur f ON a.id_fournisseur = f.id_fournisseur"  ,
"SELECT f.nom_fournisseur, COUNT(a.id_produit) AS nombre_produits FROM Fournisseur f JOIN Approvisionnement a ON f.id_fournisseur = a.id_fournisseur GROUP BY f.nom_fournisseur",
"SELECT p.nom_produit, p.prix FROM Produit p WHERE p.prix > 50",
"SELECT c.*, cl.nom, cl.adresse FROM Commande c JOIN Client cl ON c.id_client = cl.id_client WHERE c.date_commande BETWEEN '2023-01-01' AND '2023-12-31'",
"SELECT AVG(p.prix) AS prix_moyen FROM Produit p",
"SELECT COUNT(*) AS total_commandes FROM Commande",
"SELECT f.*, COUNT(a.id_produit) AS nombre_produits FROM Fournisseur f JOIN Approvisionnement a ON f.id_fournisseur = a.id_fournisseur GROUP BY f.id_fournisseur, f.nom_fournisseur, f.adresse_fournisseur",
"SELECT c.nom, COUNT(cmd.id_commande) AS total_commandes FROM Client c LEFT JOIN Commande cmd ON c.id_client = cmd.id_client GROUP BY c.nom",
"SELECT p.nom_produit, SUM(lc.quantite) AS quantite_totale_vendue FROM Produit p JOIN Ligne_Commande lc ON p.id_produit = lc.id_produit GROUP BY p.nom_produit",
"SELECT f.nom_fournisseur, AVG(a.quantite) AS quantite_moyenne_approvisionnement FROM Fournisseur f JOIN Approvisionnement a ON f.id_fournisseur = a.id_fournisseur GROUP BY f.nom_fournisseur",
"SELECT c.nom, COUNT(DISTINCT cmd.date_commande) AS jours_differents_commande FROM Client c JOIN Commande cmd ON c.id_client = cmd.id_client GROUP BY c.nom",
"SELECT p.nom_produit, COUNT(lc.id_ligne) AS nombre_ventes FROM Produit p JOIN Ligne_Commande lc ON p.id_produit = lc.id_produit GROUP BY p.nom_produit ORDER BY COUNT(lc.id_ligne) DESC",
"SELECT f.nom_fournisseur, COUNT(a.id_approv) AS nombre_approvisionnements FROM Fournisseur f JOIN Approvisionnement a ON f.id_fournisseur = a.id_fournisseur GROUP BY f.nom_fournisseur ORDER BY COUNT(a.id_approv) DESC" ,
"UPDATE Client SET adresse = 'Nouvelle adresse' WHERE id_client = 1",
"UPDATE Produit SET prix = prix * 1.1 WHERE prix < 100",
"UPDATE Fournisseur SET nom_fournisseur = 'Nouveau fournisseur' WHERE id_fournisseur = 1",
"UPDATE Commande SET date_commande = NOW() WHERE id_commande = 1",
"UPDATE Ligne_Commande SET quantite = quantite + 10 WHERE id_ligne = 1" ,
"UPDATE Produit SET prix = prix * 0.9 WHERE prix > 100",
"UPDATE Client SET nom = 'Nouveau nom' WHERE id_client = 2",
"UPDATE Approvisionnement SET quantite = quantite - 5 WHERE id_fournisseur = 1",
"UPDATE Commande SET date_commande = '2023-06-15' WHERE date_commande < '2023-06-15'",
"UPDATE Ligne_Commande SET quantite = quantite - 2 WHERE id_produit = 1" ,
"SELECT * FROM Client WHERE adresse LIKE '%Paris%'",
"SELECT COUNT(*) FROM Commande",
"SELECT AVG(prix) FROM Produit",
"SELECT p.nom_produit, SUM(lc.quantite) AS quantite_totale FROM Ligne_Commande lc JOIN Produit p ON lc.id_produit = p.id_produit GROUP BY p.nom_produit LIMIT 0, 25",
"SELECT f.nom_fournisseur, COUNT(*) AS nombre_approvisionnements FROM Approvisionnement a JOIN Fournisseur f ON a.id_fournisseur = f.id_fournisseur GROUP BY f.nom_fournisseur LIMIT 0, 25;",
"SELECT * FROM Client WHERE adresse LIKE '%Paris%' OR adresse LIKE '%Lyon%'",
"SELECT * FROM Commande WHERE date_commande BETWEEN '2023-01-01' AND '2023-12-31' OR id_client = 2",
"SELECT * FROM Produit WHERE prix > 50 OR (id_produit IN (SELECT id_produit FROM Ligne_Commande GROUP BY id_produit HAVING SUM(quantite) < 10))",
"SELECT * FROM Fournisseur WHERE id_fournisseur IN (SELECT id_fournisseur FROM Approvisionnement GROUP BY id_fournisseur HAVING COUNT(id_produit) > 100) OR nom_fournisseur LIKE 'Fournisseur%'",
"SELECT * FROM Ligne_Commande WHERE quantite > 20 OR id_commande IN (SELECT id_commande FROM Commande WHERE date_commande < '2023-06-15')",
"UPDATE Produit SET prix = 120 WHERE nom_produit LIKE 'Produit%' OR (id_produit IN (SELECT id_produit FROM Ligne_Commande GROUP BY id_produit HAVING SUM(quantite) > 50))",
"SELECT * FROM countries WHERE countries.country_name IN ('Germany', 'Turkey')",
"SELECT /*+ INDEX(countries idx_country_name) */ * FROM countries WHERE (countries.country_name ='Germany' OR countries.country_name ='Turkey')",
"SELECT /*+ INDEX(countries idx_country_name) */ * FROM countries WHERE countries.country_name IN ('Germany', 'Turkey')"
]

execution_times = [0.0004 , 0.0004 , 0.0004 ,  0.0004 , 0.0006 ,0.0006 , 0.0003 , 0.0003 , 0.0003, 0.0003, 0.0003, 0.0002, 0.0003 , 0.0004, 0.0005, 0.0005, 0.0004, 0.0004, 0.0005  , 0.0003, 0.0002, 0.0008, 0.0007, 0.0008 , 0.0003, 0.0004, 0.0004, 0.0004, 0.0003 , 0.0003, 0.0002, 0.0003 , 0.0004, 0.0004 , 0.0002 , 0.0003 , 0.0003 ,0.0005 , 0.0004  , 0.0003, 0.0003, 0.0002, 0.0001]  # Corresponding execution times

# Feature extraction using TF-IDF vectorization
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(queries)

# Train a linear regression model
model = LinearRegression()
model.fit(X, execution_times)

# Save the trained model and vectorizer to files
joblib.dump(model, 'linear_regression_model.joblib')
joblib.dump(vectorizer, 'tfidf_vectorizer.joblib')
