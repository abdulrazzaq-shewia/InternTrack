-- Generated SQLite schema; application also initializes this automatically.
PRAGMA foreign_keys=ON;

CREATE TABLE application (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	company VARCHAR(100) NOT NULL, 
	position VARCHAR(150) NOT NULL, 
	applied_date DATE NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	job_url VARCHAR(1000) NOT NULL, 
	interview_datetime DATETIME, 
	notes TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT valid_status CHECK (status IN ('Applied','Interview','Offer','Rejected','Withdrawn')), 
	FOREIGN KEY(user_id) REFERENCES user (id)
);

CREATE TABLE user (
	id INTEGER NOT NULL, 
	username VARCHAR(40) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);

CREATE INDEX ix_application_user_id ON application (user_id);
