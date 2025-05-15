CREATE TABLE IF NOT EXISTS auth_user (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR (255) NOT NULL,
    password VARCHAR (255) NOT NULL
);

CREATE TABLE audio_files (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    audio_key VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audio_files_email ON audio_files(email);

--Add Username and Password for Admin User

INSERT INTO auth_user (email, password) VALUES ('michaeloppong731@gmail.com', '123456');