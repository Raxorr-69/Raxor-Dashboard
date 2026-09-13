import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import Button from "../components/common/Button";
import Card from "../components/common/Card";
import ErrorState from "../components/common/ErrorState";
import Input from "../components/common/Input";
import Loader from "../components/common/Loader";
import UserProfile from "../components/users/UserProfile";
import UserTable from "../components/users/UserTable";
import { getUserProfile, listUsers } from "../api/users";
import { useApi } from "../hooks/useApi";
import { useGuild } from "../hooks/useGuild";

const PAGE_SIZE = 25;

function UsersList({ guildId }) {
  const [sort, setSort] = useState("xp");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [offset, setOffset] = useState(0);

  const { data, loading, error, refetch } = useApi(
    () => listUsers(guildId, { sort, search, limit: PAGE_SIZE, offset }),
    [guildId, sort, search, offset]
  );

  const handleSearch = (event) => {
    event.preventDefault();
    setOffset(0);
    setSearch(searchInput.trim());
  };

  return (
    <div>
      <h1>Users</h1>
      <p>Every member Raxor has tracked activity for in this server.</p>

      <Card>
        <form className="inline-form" onSubmit={handleSearch}>
          <Input
            label="Search by user ID"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="123456789012345678"
          />
          <Button type="submit">Search</Button>
        </form>

        {error ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : loading ? (
          <Loader label="Loading users…" />
        ) : (
          <>
            <UserTable
              guildId={guildId}
              users={data.items}
              sort={sort}
              onSortChange={(value) => {
                setOffset(0);
                setSort(value);
              }}
            />
            <div className="inline-form">
              <Button
                variant="secondary"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={!data.has_more}
                onClick={() => setOffset(offset + PAGE_SIZE)}
              >
                Next
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

function UserProfilePage({ guildId, userId }) {
  const { data, loading, error, refetch } = useApi(
    () => getUserProfile(guildId, userId),
    [guildId, userId]
  );

  return (
    <div>
      <Link to={`/dashboard/${guildId}/users`}>&larr; Back to users</Link>
      <h1>Member profile</h1>

      {loading ? (
        <Loader label="Loading profile…" />
      ) : error ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : (
        <Card>
          <UserProfile user={data} />
        </Card>
      )}
    </div>
  );
}

export default function Users() {
  const { guildId } = useGuild();
  const { userId } = useParams();

  return userId ? (
    <UserProfilePage guildId={guildId} userId={userId} />
  ) : (
    <UsersList guildId={guildId} />
  );
}
